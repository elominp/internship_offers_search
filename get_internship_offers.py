#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lib.indeed import parse_indeed_offers
from lib.jobisjob import parse_jobisjob_offers
from lib.letudiant import parse_letudiant_offers
from lib.ouestfrance import parse_ouest_france_offers
from lib.ouestjob import parse_ouestjob_offers
from json import dumps


if __name__ == "__main__":
    offers = parse_indeed_offers() + parse_jobisjob_offers() + \
             parse_letudiant_offers() + parse_ouest_france_offers() + \
             parse_ouestjob_offers()
    while {} in offers:
        offers.remove({})
    print(dumps(offers))
