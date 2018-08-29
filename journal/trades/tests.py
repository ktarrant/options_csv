from django.test import TestCase

from .models import Leg
from .tastyworks_trades import load_tastyworks_trades

class TradeLegTestCase(TestCase):
    def setUp(self):
        for leg in load_tastyworks_trades("../sample/tastyworks_sample.csv"):
            leg.save()

    def test_options_legs(self):
        """ Validate the options legs """
        calls_opened = Leg.objects.filter(instrument="call", open_or_close="open")
        for call in calls_opened:
            print(call)

        # put_options = Leg.objects.filter(instrument="put")
