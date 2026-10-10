"""Browser acceptance tests for the five PRD section 13 journeys."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from uuid import uuid4

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from app.timeutils import now_ist

pytestmark = pytest.mark.e2e

WAIT_SECONDS = 10


@dataclass(frozen=True)
class Account:
    name: str
    email: str
    password: str = "browser-test-password"


def _wait(driver) -> WebDriverWait:
    return WebDriverWait(driver, WAIT_SECONDS)


def _visible_id(driver, element_id: str):
    return _wait(driver).until(ec.visibility_of_element_located((By.ID, element_id)))


def _click_id(driver, element_id: str) -> None:
    _wait(driver).until(ec.element_to_be_clickable((By.ID, element_id))).click()


def _account(role: str) -> Account:
    suffix = uuid4().hex[:10]
    return Account(
        name=f"{role.title()} {suffix}",
        email=f"{role}-{suffix}@example.com",
    )


def _register(
    driver, base_url: str, account: Account, role: str, city: str = ""
) -> None:
    driver.get(f"{base_url}/register")
    _visible_id(driver, "name").send_keys(account.name)
    _visible_id(driver, "email").send_keys(account.email)
    _visible_id(driver, "password").send_keys(account.password)
    Select(_visible_id(driver, "role")).select_by_value(role)
    if city:
        _visible_id(driver, "city").send_keys(city)
    _click_id(driver, "submit-register")
    _wait(driver).until(
        ec.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '[data-testid="nav-user"]'), account.name
        )
    )


def _login(driver, base_url: str, account: Account) -> None:
    driver.get(f"{base_url}/login")
    _visible_id(driver, "email").send_keys(account.email)
    _visible_id(driver, "password").send_keys(account.password)
    _click_id(driver, "submit-login")
    _wait(driver).until(
        ec.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '[data-testid="nav-user"]'), account.name
        )
    )


def _logout(driver) -> None:
    _wait(driver).until(
        ec.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="nav-logout"]'))
    ).click()
    _wait(driver).until(
        ec.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="nav-login"]'))
    )


def _set_datetime_local(driver, element_id: str, value: str) -> None:
    element = _visible_id(driver, element_id)
    driver.execute_script(
        """
        arguments[0].value = arguments[1];
        arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
        arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
        """,
        element,
        value,
    )


def _create_slot(driver, base_url: str, city: str, title: str) -> None:
    start_at = now_ist().replace(second=0, microsecond=0) + timedelta(days=2)
    end_at = start_at + timedelta(hours=2)
    driver.get(f"{base_url}/guide/slots/new")
    _visible_id(driver, "title").send_keys(title)
    _set_datetime_local(driver, "start_at", start_at.strftime("%Y-%m-%dT%H:%M"))
    _set_datetime_local(driver, "end_at", end_at.strftime("%Y-%m-%dT%H:%M"))
    _visible_id(driver, "price_inr").send_keys("1500")
    _click_id(driver, "submit-slot")
    _wait(driver).until(
        ec.visibility_of_element_located(
            (By.CSS_SELECTOR, '[data-testid="guide-slot-row"]')
        )
    )


def _open_public_slot(driver, base_url: str, city: str) -> None:
    driver.get(f"{base_url}/slots")
    city_filter = _visible_id(driver, "filter-city")
    city_filter.clear()
    city_filter.send_keys(city)
    _click_id(driver, "apply-filter")
    _wait(driver).until(
        ec.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="slot-link"]'))
    ).click()


def _request_booking(driver, base_url: str, city: str, note: str) -> None:
    _open_public_slot(driver, base_url, city)
    _visible_id(driver, "note").send_keys(note)
    _click_id(driver, "book-btn")
    _wait(driver).until(
        ec.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="flash"]'))
    )


def _booking_detail_from_list(driver) -> None:
    _wait(driver).until(
        ec.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="booking-row"] a'))
    ).click()


def _create_requested_booking(driver, base_url: str):
    city = f"City-{uuid4().hex[:8]}"
    guide = _account("guide")
    traveler = _account("traveler")
    title = f"Walking tour {uuid4().hex[:8]}"

    _register(driver, base_url, guide, "guide", city)
    _create_slot(driver, base_url, city, title)
    _logout(driver)
    _register(driver, base_url, traveler, "traveler")
    _request_booking(driver, base_url, city, "Please reserve this experience.")
    return guide, traveler, city


def test_j1_registration_and_login(driver, base_url: str) -> None:
    """J1: a traveler can register, log out, and log back in."""
    traveler = _account("traveler")

    _register(driver, base_url, traveler, "traveler")
    _logout(driver)
    _login(driver, base_url, traveler)


def test_j2_guide_publishes_availability(driver, base_url: str) -> None:
    """J2: a guide-created future slot is visible through the city filter."""
    city = f"City-{uuid4().hex[:8]}"
    guide = _account("guide")
    title = f"Market walk {uuid4().hex[:8]}"

    _register(driver, base_url, guide, "guide", city)
    _create_slot(driver, base_url, city, title)
    _logout(driver)
    _open_public_slot(driver, base_url, city)
    _wait(driver).until(ec.title_contains(title))


def test_j3_booking_request(driver, base_url: str) -> None:
    """J3: a traveler requests a slot and sees PENDING in My Bookings."""
    _create_requested_booking(driver, base_url)

    _wait(driver).until(
        ec.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="nav-bookings"]'))
    ).click()
    _wait(driver).until(
        ec.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '[data-testid="booking-status"]'), "PENDING"
        )
    )


def test_j4_guide_confirms_booking(driver, base_url: str) -> None:
    """J4: confirmation is visible to the traveler and hides the public slot."""
    guide, traveler, city = _create_requested_booking(driver, base_url)

    _logout(driver)
    _login(driver, base_url, guide)
    _wait(driver).until(
        ec.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="nav-bookings"]'))
    ).click()
    _booking_detail_from_list(driver)
    _click_id(driver, "confirm-btn")
    _wait(driver).until(
        ec.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '[data-testid="booking-status"]'), "CONFIRMED"
        )
    )

    _logout(driver)
    _login(driver, base_url, traveler)
    _wait(driver).until(
        ec.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="nav-bookings"]'))
    ).click()
    _wait(driver).until(
        ec.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '[data-testid="booking-status"]'), "CONFIRMED"
        )
    )
    _open_public_slot_list(driver, base_url, city)
    _wait(driver).until(
        ec.visibility_of_element_located(
            (By.CSS_SELECTOR, '[data-testid="empty-state"]')
        )
    )


def test_j5_traveler_cancels_confirmed_booking(driver, base_url: str) -> None:
    """J5: cancellation restores availability and adds the third timeline event."""
    guide, traveler, city = _create_requested_booking(driver, base_url)

    _logout(driver)
    _login(driver, base_url, guide)
    _wait(driver).until(
        ec.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="nav-bookings"]'))
    ).click()
    _booking_detail_from_list(driver)
    _click_id(driver, "confirm-btn")
    _wait(driver).until(
        ec.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '[data-testid="booking-status"]'), "CONFIRMED"
        )
    )

    _logout(driver)
    _login(driver, base_url, traveler)
    _wait(driver).until(
        ec.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="nav-bookings"]'))
    ).click()
    _booking_detail_from_list(driver)
    _visible_id(driver, "reason").send_keys("Plans changed.")
    _click_id(driver, "cancel-btn")
    _wait(driver).until(
        ec.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '[data-testid="booking-status"]'), "CANCELLED"
        )
    )
    _wait(driver).until(
        lambda browser: len(
            browser.find_elements(By.CSS_SELECTOR, '[data-testid="timeline-item"]')
        )
        == 3
    )
    _open_public_slot_list(driver, base_url, city)
    _wait(driver).until(
        ec.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="slot-row"]'))
    )


def _open_public_slot_list(driver, base_url: str, city: str) -> None:
    driver.get(f"{base_url}/slots")
    city_filter = _visible_id(driver, "filter-city")
    city_filter.clear()
    city_filter.send_keys(city)
    _click_id(driver, "apply-filter")
