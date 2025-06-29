import json
import os
from datetime import datetime, timedelta, date, time
from dateutil import tz
from unittest.mock import Mock

from tesla_tou_settings import (
    TouPeriod,
    TouPeriodContainer,
    Season,
    EnergyChargesSeason,
    DailyCharge,
    SellTariff,
    TimeOfUseSettings,
    DemandChargesSeason,
)
from price_updater import PowerwallPriceUpdater
from simple_price import PriceType, SimplePrice
import pytest


@pytest.fixture
def mock_clients():
    globird_client_mock = Mock()
    amber_client_mock = Mock()
    return globird_client_mock, amber_client_mock


def test_build_time_of_use_settings_with_example_data(mock_clients):
    globird_client_mock, amber_client_mock = mock_clients

    # Set the RESOLUTION environment variable for the test
    os.environ["RESOLUTION"] = "5"

    today = date.today()
    resolution_minutes = int(os.environ.get("RESOLUTION"))

    # Mock prices for Globird and Amber
    globird_prices = []
    amber_prices = []
    current_time = datetime.combine(today, time(0, 0), tzinfo=tz.tzlocal())
    end_time = datetime.combine(today, time(23, 55), tzinfo=tz.tzlocal())

    while current_time <= end_time:
        globird_prices.append(
            SimplePrice(
                start_time=current_time,
                period=timedelta(minutes=resolution_minutes),
                buy_per_kwh=0.25,
                sell_per_kwh=0.10,
                price_type=PriceType.ACTUAL,
            )
        )
        # Amber prices will have a higher sell price for a specific period to test the logic
        amber_sell_price = 0.10
        if current_time.hour == 17:  # Example: 5 PM
            amber_sell_price = 1.55  # Above sell_threshold
        amber_prices.append(
            SimplePrice(
                start_time=current_time,
                period=timedelta(minutes=resolution_minutes),
                buy_per_kwh=0.20,  # Dummy buy price for Amber
                sell_per_kwh=amber_sell_price,
                price_type=PriceType.FORECAST,
            )
        )
        current_time += timedelta(minutes=resolution_minutes)

    globird_client_mock.get_prices.return_value = globird_prices
    amber_client_mock.get_forecast.return_value = amber_prices

    # Instantiate PowerwallPriceUpdater with mocked clients
    updater = PowerwallPriceUpdater(
        globird_client=globird_client_mock, amber_client=amber_client_mock
    )

    # Generate combined prices using the updater's internal logic
    combined_prices = updater._generate_prices()

    # Manually construct the expected_tou_settings based on _build_time_of_use_settings logic
    tou_periods_list = []
    buy_rates_dict = {}
    sell_rates_dict = {}

    for price in combined_prices:  # Use combined_prices here
        start_time_str = price.start_time.strftime("%H%M")
        end_time_period = price.start_time + price.period

        tou_periods_list.append(
            TouPeriod(
                fromDayOfWeek=0,
                toHour=end_time_period.hour,
                toDayOfWeek=6,
                fromHour=price.start_time.hour,
                fromMinute=price.start_time.minute,
                toMinute=end_time_period.minute,
            )
        )
        buy_rates_dict[start_time_str] = price.buy_per_kwh
        sell_rates_dict[start_time_str] = price.sell_per_kwh

    tou_period_container = TouPeriodContainer(periods=tou_periods_list)

    main_season = Season(
        fromMonth=1,
        fromDay=1,
        toMonth=12,
        toDay=31,
        tou_periods={"ALL": tou_period_container},
    )

    main_energy_charges_season = EnergyChargesSeason(rates=buy_rates_dict)
    main_energy_charges = {"ALL": main_energy_charges_season}

    sell_energy_charges_season = EnergyChargesSeason(rates=sell_rates_dict)
    sell_energy_charges = {"ALL": sell_energy_charges_season}

    daily_charge_obj = DailyCharge(name="Daily Charge", amount=1.1)

    default_demand_charges_season = DemandChargesSeason(rates={})
    default_demand_charges = {"ALL": default_demand_charges_season}

    sell_tariff_obj = SellTariff(
        min_applicable_demand=0.0,
        monthly_minimum_bill=0.0,
        monthly_charges=0.0,
        max_applicable_demand=0.0,
        utility="Globird",
        demand_charges=default_demand_charges,
        daily_charges=[daily_charge_obj],
        seasons={"ALL": main_season},
        code="ZEROHERO",
        energy_charges=sell_energy_charges,
        daily_demand_charges={},
        currency="USD",
        name="Globird ZEROHERO VPP",
    )

    expected_tou_settings = TimeOfUseSettings(
        version=1,
        monthly_minimum_bill=0.0,
        min_applicable_demand=0.0,
        max_applicable_demand=0.0,
        monthly_charges=0.0,
        utility="Globird",
        code="ZEROHERO",
        name="Globird ZEROHERO VPP",
        currency="USD",
        daily_charges=[daily_charge_obj],
        daily_demand_charges={},
        demand_charges=default_demand_charges,
        energy_charges=main_energy_charges,
        seasons={"ALL": main_season},
        sell_tariff=sell_tariff_obj,
    )

    # Call the method under test with combined_prices
    actual_tou_settings = updater._build_time_of_use_settings(combined_prices)

    # Add assertion for the price at 5 PM where the sell price is above the threshold
    five_pm_price = next(
        (
            price
            for price in combined_prices
            if price.start_time.hour == 17 and price.start_time.minute == 0
        ),
        None,
    )
    assert five_pm_price is not None, "Price for 5 PM not found in combined_prices"
    assert five_pm_price.sell_per_kwh == 1, "Sell price at 5 PM should be 1"

    print("Expected TOU Settings:", expected_tou_settings.to_dict())
    print("Actual TOU Settings:", actual_tou_settings.to_dict())

    # Compare the actual result with the expected result
    assert actual_tou_settings == expected_tou_settings

    # Clean up the environment variable
    del os.environ["RESOLUTION"]
