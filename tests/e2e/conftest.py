"""Selenium fixtures shared by live-application acceptance tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


@pytest.fixture
def base_url() -> str:
    """Use a live target so the same suite can run locally or against a Grid."""
    return os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")


@pytest.fixture
def driver():
    """Create one isolated browser session per acceptance journey."""
    options = Options()
    if os.getenv("E2E_HEADLESS", "1") == "1":
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--window-size=1440,1200")

    remote_url = os.getenv("SELENIUM_REMOTE_URL")
    if remote_url:
        browser = webdriver.Remote(command_executor=remote_url, options=options)
    else:
        driver_path = os.getenv("CHROMEDRIVER_PATH")
        service = Service(executable_path=driver_path) if driver_path else Service()
        browser = webdriver.Chrome(service=service, options=options)

    yield browser
    browser.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[object]):
    """Persist browser state when a journey fails, without hiding the failure."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return

    browser = item.funcargs.get("driver")
    if browser is None:
        return

    artifact_dir = Path("test-artifacts")
    artifact_dir.mkdir(exist_ok=True)
    safe_name = item.name.replace("/", "_").replace("\\", "_")
    try:
        browser.save_screenshot(str(artifact_dir / f"{safe_name}.png"))
    except WebDriverException:
        # A crashed browser cannot produce an artifact; retain the original test error.
        return
