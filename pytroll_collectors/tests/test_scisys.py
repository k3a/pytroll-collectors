#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2023 Pytroll developers
#
# Author(s):
#
#   Martin Raspaud <martin.raspaud@smhi.se>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Test suite for the scisys receiver."""


# Test cases.

import datetime
import os
from unittest import TestCase
import pytest
from copy import deepcopy
import tempfile

from pytroll_collectors.scisys import MessageReceiver, TwoMetMessage
from pytroll_collectors.scisys import get_subject_from_msg2send

hostname = 'localhost'

input_stoprc = '<message timestamp="2013-02-18T09:21:35" sequence="7482" severity="INFO" messageID="0" type="2met.message" sourcePU="SMHI-Linux" sourceSU="POESAcquisition" sourceModule="POES" sourceInstance="1"><body>STOPRC Stop reception: Satellite: NPP, Orbit number: 6796, Risetime: 2013-02-18 09:08:09, Falltime: 2013-02-18 09:21:33</body></message>'  # noqa


def create_input_dispatch_viirs_msg(dirname):
    """Create dispatch message for VIIRS scene."""
    return '<message timestamp="2013-02-18T09:24:20" sequence="27098" severity="INFO" messageID="8250" type="2met.filehandler.sink.success" sourcePU="SMHI-Linux" sourceSU="GMCSERVER" sourceModule="GMCSERVER" sourceInstance="1"><body>FILDIS File Dispatch: /data/npp/RNSCA-RVIRS_npp_d20130218_t0908103_e0921256_b00001_c20130218092411165000_nfts_drl.h5 ftp://{hostname}:21{path}/RNSCA-RVIRS_npp_d20130218_t0908103_e0921256_b00001_c20130218092411165000_nfts_drl.h5</body></message>'.format(hostname=hostname, path=dirname)  # noqa


def create_input_dispatch_atms_msg(dirname):
    """Create dispatch message for ATMS scene."""
    return '<message timestamp="2013-02-18T09:24:21" sequence="27100" severity="INFO" messageID="8250" type="2met.filehandler.sink.success" sourcePU="SMHI-Linux" sourceSU="GMCSERVER" sourceModule="GMCSERVER" sourceInstance="1"><body>FILDIS File Dispatch: /data/npp/RATMS-RNSCA_npp_d20130218_t0908194_e0921055_b00001_c20130218092411244000_nfts_drl.h5 ftp://{hostname}:21{path}/RATMS-RNSCA_npp_d20130218_t0908194_e0921055_b00001_c20130218092411244000_nfts_drl.h5</body></message>'.format(hostname=hostname, path=dirname)  # noqa


INPUT_DISPATCH = {}
INPUT_DISPATCH['viirs'] = create_input_dispatch_viirs_msg('/tmp')
INPUT_DISPATCH['atms'] = create_input_dispatch_atms_msg('/tmp')


VIIRS = {'platform_name': 'Suomi-NPP', 'format': 'RDR',
         'start_time': datetime.datetime(2013, 2, 18, 9, 8, 10, 300000),
         'data_processing_level': '0', 'orbit_number': 6796,
         'uri': 'ssh://{hostname}/tmp/RNSCA-RVIRS_npp_d20130218_t0908103_e0921256_b00001_c20130218092411165000_nfts_drl.h5'.format(hostname=hostname),  # noqa
         'uid': 'RNSCA-RVIRS_npp_d20130218_t0908103_e0921256_b00001_c20130218092411165000_nfts_drl.h5',
         'sensor': 'viirs',
         'end_time': datetime.datetime(2013, 2, 18, 9, 21, 25, 600000),
         'type': 'HDF5', 'variant': 'DR'}

ATMS = {'platform_name': 'Suomi-NPP', 'format': 'RDR', 'start_time':
        datetime.datetime(2013, 2, 18, 9, 8, 19, 400000),
        'data_processing_level': '0', 'orbit_number': 6796, 'uri':
        'ssh://{hostname}/tmp/RATMS-RNSCA_npp_d20130218_t0908194_e0921055_b00001_c20130218092411244000_nfts_drl.h5'.format(  # noqa
            hostname=hostname),
        'uid':
        'RATMS-RNSCA_npp_d20130218_t0908194_e0921055_b00001_c20130218092411244000_nfts_drl.h5',
        'sensor': 'atms',
        'end_time': datetime.datetime(2013, 2, 18, 9, 21, 5, 500000),
        'type': 'HDF5', 'variant': 'DR'}

stoprc_terra = '<message timestamp="2014-10-30T21:03:50" sequence="6153" severity="INFO" messageID="0" type="2met.message" sourcePU="SMHI-Linux" sourceSU="POESAcquisition" sourceModule="POES" sourceInstance="1"><body>STOPRC Stop reception: Satellite: TERRA, Orbit number: 79082, Risetime: 2014-10-30 20:49:50, Falltime: 2014-10-30 21:03:50</body></message>'  # noqa


def create_fildis_terra(dirname):
    """Create dispatch message for Terra file."""
    return '<message timestamp="2014-10-30T21:03:57" sequence="213208" severity="INFO" messageID="8250" type="2met.filehandler.sink.success" sourcePU="SMHI-Linux" sourceSU="GMCSERVER" sourceModule="GMCSERVER" sourceInstance="1"><body>FILDIS File Dispatch: /data/modis/P0420064AAAAAAAAAAAAAA14303204950001.PDS ftp://{hostname}:21{path}/P0420064AAAAAAAAAAAAAA14303204950001.PDS</body></message>'.format(hostname=hostname, path=dirname)  # noqa


def create_msg_terra(dirname):
    """Create message data for Terra scene."""
    return {"platform_name": "EOS-Terra", "uri":
            "ssh://{hostname}{path}/P0420064AAAAAAAAAAAAAA14303204950001.PDS".format(hostname=hostname, path=dirname),
            "format": "PDS",
            "start_time": datetime.datetime(2014, 10, 30, 20, 49, 50),
            "data_processing_level": "0", "orbit_number": 79082, "uid":
            "P0420064AAAAAAAAAAAAAA14303204950001.PDS",
            "sensor": "modis",
            "end_time": datetime.datetime(2014, 10, 30, 21, 3, 50),
            "type": "binary", 'variant': 'DR'}


stoprc_n19 = '<message timestamp="2014-10-28T07:25:37" sequence="472" severity="INFO" messageID="0" type="2met.message" sourcePU="SMHI-Linux" sourceSU="HRPTAcquisition" sourceModule="FSSRVC" sourceInstance="1"><body>STOPRC Stop reception: Satellite: NOAA 19, Orbit number: 29477, Risetime: 2014-10-28 07:16:01, Falltime: 2014-10-28 07:25:37</body></message>'  # noqa


def create_fildis_n19(dirname):
    """Create dispatch message for NOAA-19."""
    return '<message timestamp="2014-10-28T07:25:43" sequence="203257" severity="INFO" messageID="8250" type="2met.filehandler.sink.success" sourcePU="SMHI-Linux" sourceSU="GMCSERVER" sourceModule="GMCSERVER" sourceInstance="1"><body>FILDIS File Dispatch: /data/hrpt/20141028071601_NOAA_19.hmf ftp://{hostname}:21{path}/20141028071601_NOAA_19.hmf</body></message>'.format(hostname=hostname, path=dirname)   # noqa


def create_msg_n19(dirname):
    """Create message data for NOAA-19 scene."""
    return {"platform_name": "NOAA-19", "format": "HRPT",
            "start_time": datetime.datetime(2014, 10, 28, 7, 16, 1),
            "data_processing_level": "0", "orbit_number": 29477,
            "uri": "ssh://{hostname}{path}/20141028071601_NOAA_19.hmf".format(hostname=hostname, path=dirname),
            "uid": "20141028071601_NOAA_19.hmf",
            "sensor": ("avhrr/3", "mhs", "amsu-a", "hirs/4"),
            "end_time": datetime.datetime(2014, 10, 28, 7, 25, 37),
            "type": "binary", 'variant': 'DR'}


stoprc_m01 = '<message timestamp="2014-10-28T08:45:22" sequence="1157" severity="INFO" messageID="0" type="2met.message" sourcePU="SMHI-Linux" sourceSU="HRPTAcquisition" sourceModule="FSSRVC" sourceInstance="1"><body>STOPRC Stop reception: Satellite: METOP-B, Orbit number: 10948, Risetime: 2014-10-28 08:30:10, Falltime: 2014-10-28 08:45:22</body></message>'  # noqa


def create_fildis_m01(dirname):
    """Create message for Metop-B scene."""
    return '<message timestamp="2014-10-28T08:45:27" sequence="203535" severity="INFO" messageID="8250" type="2met.filehandler.sink.success" sourcePU="SMHI-Linux" sourceSU="GMCSERVER" sourceModule="GMCSERVER" sourceInstance="1"><body>FILDIS File Dispatch: /data/metop/MHSx_HRP_00_M01_20141028083003Z_20141028084510Z_N_O_20141028083010Z ftp://{hostname}:21{path}/MHSx_HRP_00_M01_20141028083003Z_20141028084510Z_N_O_20141028083010Z</body></message>'.format(hostname=hostname, path=dirname)  # noqa


def create_msg_m01(dirname):
    """Create message data for Metop-B scene."""
    return {"platform_name": "Metop-B",
            "format": "EPS",
            "start_time": datetime.datetime(2014, 10, 28, 8, 30, 3),
            "data_processing_level": "0",
            "orbit_number": 10948,
            "uri": "ssh://{hostname}{path}/MHSx_HRP_00_M01_20141028083003Z_20141028084510Z_N_O_20141028083010Z".format(hostname=hostname, path=dirname),  # noqa
            "uid": "MHSx_HRP_00_M01_20141028083003Z_20141028084510Z_N_O_20141028083010Z",
            "sensor": "mhs",
            "end_time": datetime.datetime(2014, 10, 28, 8, 45, 10),
            "type": "binary", 'variant': 'DR'}


startrc_npp2 = '<message timestamp="2014-10-31T08:53:52" sequence="9096" severity="INFO" messageID="0" type="2met.message" sourcePU="SMHI-Linux" sourceSU="POESAcquisition" sourceModule="POES" sourceInstance="1"><body>STRTRC Start reception: Satellite: NPP, Orbit number: 15591, Risetime: 2014-10-31 08:53:52, Falltime: 2014-10-31 09:06:28</body></message>'  # noqa

stoprc_npp2 = '<message timestamp="2014-10-31T09:06:28" sequence="9340" severity="INFO" messageID="0" type="2met.message" sourcePU="SMHI-Linux" sourceSU="POESAcquisition" sourceModule="POES" sourceInstance="1"><body>STOPRC Stop reception: Satellite: NPP, Orbit number: 15591, Risetime: 2014-10-31 08:53:52, Falltime: 2014-10-31 09:06:28</body></message>'  # noqa


def create_fildis_npp2(dirname):
    """Create message for Suomi-NPP scene."""
    return '<message timestamp="2014-10-31T09:06:25" sequence="216010" severity="INFO" messageID="8250" type="2met.filehandler.sink.success" sourcePU="SMHI-Linux" sourceSU="GMCSERVER" sourceModule="GMCSERVER" sourceInstance="1"><body>FILDIS File Dispatch: /data/npp/RCRIS-RNSCA_npp_d20141031_t0905166_e0905484_b00001_c20141031090623200000_nfts_drl.h5 ftp://{hostname}:21/{path}</body></message>'.format(hostname=hostname, path=dirname)  # noqa


def create_msg_npp2(dirname):
    """Create message data for Suomi-NPP scene."""
    return {"orbit_number": 15591,
            "uid": "RCRIS-RNSCA_npp_d20141031_t0905166_e0905484_b00001_c20141031090623200000_nfts_drl.h5",
            "format": "RDR", "sensor": "cris",
            "start_time": datetime.datetime(2014, 10, 31, 9, 5, 16, 600000),
            "uri": "ssh://{hostname}/{path}/RCRIS-RNSCA_npp_d20141031_t0905166_e0905484_b00001_c20141031090623200000_nfts_drl.h5".format(hostname=hostname, path=dirname),  # noqa
            "platform_name": "Suomi-NPP",
            "end_time": datetime.datetime(2014, 10, 31, 9, 5, 48, 400000),
            "type": "HDF5", "data_processing_level": "0", 'variant': 'DR'}


def create_fildis_m03(dirname):
    """Create message for Metop-C scene."""
    return '<message timestamp="2022-12-19T18:57:45" sequence="2581" severity="INFO" messageID="0" type="2met.dispat.suctrn.info" sourcePU="MERLIN" sourceSU="Dispatch" sourceModule="DISPAT" sourceInstance="1"><body>SUCTRN AVHR_HRP_00_M03_20221219184226Z_20221219185738Z_N_O_20221219184230Z -&gt; ftp://{hostname}:21{path}</body></message>'.format(hostname=hostname, path=dirname)  # noqa


msg_m03_avhrr = {'start_time': datetime.datetime(2022, 12, 19, 18, 42, 26),
                 'end_time': datetime.datetime(2022, 12, 19, 18, 57, 38),
                 'orbit_number': 21363,
                 'platform_name': 'Metop-C',
                 'sensor': 'avhrr/3',
                 'format': 'EPS',
                 'type': 'binary',
                 'data_processing_level': '0',
                 'uid': 'AVHR_HRP_00_M03_20221219184226Z_20221219185738Z_N_O_20221219184230Z',
                 'uri': 'ssh://{hostname}/tmp/AVHR_HRP_00_M03_20221219184226Z_20221219185738Z_N_O_20221219184230Z'.format(hostname=hostname),  # noqa
                 'variant': 'DR'}


def touch(fname):
    """Create an empty file."""
    open(fname, 'a').close()


class TestScisysReceiver:
    """Testing the Scisys receiver."""

    def test_reception(self):
        """Test the reception."""
        msg_rec = MessageReceiver("nimbus")

        # NPP

        string = TwoMetMessage(input_stoprc)
        to_send = msg_rec.receive(string)
        assert to_send is None

        with tempfile.TemporaryDirectory() as tmp:
            filename = os.path.join(tmp, VIIRS['uid'])
            touch(filename)
            string = TwoMetMessage(create_input_dispatch_viirs_msg(tmp))
            to_send = msg_rec.receive(string)
            viirs_cpy = deepcopy(VIIRS)
            viirs_cpy.pop('uri')
            to_send.pop('uri')
            TestCase().assertDictEqual(to_send, viirs_cpy)
            os.remove(filename)

        with tempfile.TemporaryDirectory() as tmp:
            filename = os.path.join(tmp, ATMS['uid'])
            touch(filename)
            string = TwoMetMessage(create_input_dispatch_atms_msg(tmp))
            to_send = msg_rec.receive(string)

            atms_cpy = deepcopy(ATMS)
            atms_cpy.pop('uri')
            to_send.pop('uri')
            TestCase().assertDictEqual(to_send, atms_cpy)
            os.remove(filename)

        # # NPP with start

        string = TwoMetMessage(startrc_npp2)
        to_send = msg_rec.receive(string)
        assert to_send is None

        with tempfile.TemporaryDirectory() as tmp:
            filename = os.path.join(tmp, create_msg_npp2(tmp)['uid'])
            touch(filename)
            string = TwoMetMessage(create_fildis_npp2(tmp))
            to_send = msg_rec.receive(string)
            TestCase().assertDictEqual(to_send, create_msg_npp2(tmp))
            os.remove(filename)

        # Terra

        string = TwoMetMessage(stoprc_terra)
        to_send = msg_rec.receive(string)
        assert to_send is None

        with tempfile.TemporaryDirectory() as tmp:
            filename = os.path.join(tmp, create_msg_terra(tmp)['uid'])
            touch(filename)
            string = TwoMetMessage(create_fildis_terra(tmp))
            to_send = msg_rec.receive(string)
            TestCase().assertDictEqual(to_send, create_msg_terra(tmp))
            os.remove(filename)

        # # NOAA-19

        string = TwoMetMessage(stoprc_n19)
        to_send = msg_rec.receive(string)
        assert to_send is None

        with tempfile.TemporaryDirectory() as tmp:
            filename = os.path.join(tmp, create_msg_n19(tmp)['uid'])
            touch(filename)
            string = TwoMetMessage(create_fildis_n19(tmp))
            to_send = msg_rec.receive(string)
            TestCase().assertDictEqual(to_send, create_msg_n19(tmp))
            os.remove(filename)

        # # Metop-B

        string = TwoMetMessage(stoprc_m01)
        to_send = msg_rec.receive(string)
        assert to_send is None

        with tempfile.TemporaryDirectory() as tmp:
            filename = os.path.join(tmp, create_msg_m01(tmp)['uid'])
            touch(filename)
            string = TwoMetMessage(create_fildis_m01(tmp))
            to_send = msg_rec.receive(string)
            TestCase().assertDictEqual(to_send, create_msg_m01(tmp))
            os.remove(filename)


@pytest.mark.parametrize("sensor, sensor_name", [(VIIRS, 'viirs'),
                                                 (ATMS, 'atms')])
def test_get_subject_from_msg2send_postfix_topic_is_none(sensor, sensor_name):
    """Test the get the subject from the message being send."""
    msg_rec = MessageReceiver("nimbus")

    filename = os.path.join('/tmp', sensor['uid'])
    touch(filename)
    string = TwoMetMessage(INPUT_DISPATCH[sensor_name])
    to_send = msg_rec.receive(string)
    os.remove(filename)

    topic_postfix = None
    station = 'nrk'
    environment = 'dev'
    subject = get_subject_from_msg2send(to_send, station, environment, topic_postfix)

    assert subject == "/{sensor}/RDR/0/nrk/dev/polar/direct_readout".format(sensor=sensor_name)


@pytest.mark.parametrize("sensor, sensor_name", [(VIIRS, 'viirs'),
                                                 (ATMS, 'atms')])
def test_get_subject_from_msg2send_with_postfix_topic(sensor, sensor_name):
    """Test the get the subject from the message being send."""
    msg_rec = MessageReceiver("nimbus")

    filename = os.path.join('/tmp', sensor['uid'])
    touch(filename)
    string = TwoMetMessage(INPUT_DISPATCH[sensor_name])
    to_send = msg_rec.receive(string)
    os.remove(filename)

    station = 'nrk'
    environment = 'dev'
    topic_postfix = 'my_topic'
    subject = get_subject_from_msg2send(to_send, station, environment, topic_postfix)

    assert subject == "/{sensor}/RDR/0/my_topic".format(sensor=sensor_name)


def test_get_subject_from_msg2send_empty_postfix_topic():
    """Test get the subject from the message being send - empty postfix topic."""
    msg_rec = MessageReceiver("nimbus")

    filename = os.path.join('/tmp', ATMS['uid'])
    touch(filename)
    string = TwoMetMessage(INPUT_DISPATCH['atms'])
    to_send = msg_rec.receive(string)
    os.remove(filename)

    station = 'nrk'
    environment = 'dev'
    topic_postfix = ''
    subject = get_subject_from_msg2send(to_send, station, environment, topic_postfix)

    assert subject == "/atms/RDR/0/"


def test_get_subject_from_msg2send_avhrr3():
    """Test get the subject from the message being send - avhrr data."""
    msg_rec = MessageReceiver("nimbus")

    filename = os.path.join('/tmp', create_msg_n19('/tmp')['uid'])
    touch(filename)
    string = TwoMetMessage(create_fildis_n19('/tmp'))
    to_send = msg_rec.receive(string)
    os.remove(filename)

    station = 'nrk'
    environment = 'dev'
    topic_postfix = ''

    subject = get_subject_from_msg2send(to_send, station, environment, topic_postfix)
    assert subject == "/HRPT/0/"
