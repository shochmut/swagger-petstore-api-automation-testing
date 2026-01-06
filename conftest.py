import pytest
import base64

from Utilities.read_config import AppConfiguration
from playwright.sync_api import sync_playwright


@pytest.fixture()
def setup(request):
    configuration = AppConfiguration.get_app_configuration()
    common_info = AppConfiguration.get_common_info()
    base_url = common_info["Url"]

    # Browser options
    # Parse string boolean safely instead of eval
    headless = str(configuration["Headless"]).strip().lower() == "true"
    slow_mo = float(configuration["SlowMo"])
    launch_options = {"headless": headless, "slow_mo": slow_mo}

    # Start Playwright
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(**launch_options, args=['--start-maximized'])

    context_options = {'base_url': base_url}

    # Browser context settings
    browser_context = browser.new_context(**context_options, no_viewport=True)
    browser_context.set_default_navigation_timeout(float(configuration["DefaultNavigationTimeout"]))
    browser_context.set_default_timeout(float(configuration["DefaultTimeout"]))

    # Create Page
    page = browser_context.new_page()

    request.cls.page = page
    page.goto(base_url)

    yield page
    page.close()
    browser.close()
    playwright.stop()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item):
    """Take screenshot and embed it into the HTML report on failure."""
    outcome = yield
    report = outcome.get_result()

    if report.when in ("setup", "call"):
        if "setup" in item.funcargs and report.failed:
            page = item.funcargs["setup"]
            screenshot_bytes = page.screenshot()
            extra = getattr(report, "extra", [])
            pytest_html = item.config.pluginmanager.getplugin("html")

            if pytest_html:
                extra.append(pytest_html.extras.image(
                    base64.b64encode(screenshot_bytes).decode(), mime_type="image/png"
                ))

            report.extras = extra
