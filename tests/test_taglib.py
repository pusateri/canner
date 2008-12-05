from canner import taglib
from nose.tools import *
import simplejson
import unittest

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class TagCreateTestCase(unittest.TestCase):

    def setUp(self):
        taglib.reset()


    def test_tag_cache(self):
        t1 = taglib.tag("kind", "name")
        t2 = taglib.tag("kind", "other name")
        t3 = taglib.tag(qname="kind--name")
        assert t1 != t2
        assert t1 is t3


    def test_display_and_sort_name(self):
        t = taglib.tag("kind", "name", sort_name="sort name")
        taglib.tag("kind", "name", display_name="display name")
        print repr(t.changes)
        eq_(t.kind, "kind")
        eq_(t.name, "name")
        eq_(t.display_name, "display name")
        eq_(t.sort_name, "sort name")



    def test_ip_address_tag(self):
        t = taglib.ip_address_tag("127.0.0.1")
        eq_(t.kind, "IPv4 address")
        eq_(t.name, "127.0.0.1")
        eq_(t.sort_name, "v4 7f000001")

        t = taglib.ip_address_tag("127.0.0.1", "interface address")
        eq_(t.kind, "interface address")
        eq_(t.name, "127.0.0.1")
        eq_(t.sort_name, "v4 7f000001")

    def test_ip_subnet_tag(self):
        t = taglib.ip_subnet_tag("127.0.0.0/8")
        eq_(t.kind, "IPv4 subnet")
        eq_(t.name, "127.0.0.0/8")
        eq_(t.sort_name, "v4 7f000000/08")

        t = taglib.ip_subnet_tag("127.0.0.0/8", "interface subnet")
        eq_(t.kind, "interface subnet")
        eq_(t.name, "127.0.0.0/8")
        eq_(t.sort_name, "v4 7f000000/08")

    def test_as_number_tag(self):
        t = taglib.as_number_tag("1212")
        eq_(t.kind, "AS number")
        eq_(t.name, "1212")
        eq_(t.sort_name, "0000001212")

        t = taglib.as_number_tag("1212.4124")
        eq_(t.kind, "AS number")
        eq_(t.name, "1212.4124")
        eq_(t.sort_name, "0079433756")

        t = taglib.as_number_tag("1212.4124")
        eq_(t.kind, "AS number")
        eq_(t.name, "1212.4124")
        eq_(t.sort_name, "0079433756")


class TagLoggingTestCase(unittest.TestCase):

    def setUp(self):
        taglib.reset()

    def roundtrip(self):
        f = StringIO()
        taglib.tagging_log.dump(f)
        json = f.getvalue()
        print json
        return simplejson.loads(json)

    def test_unused_tag(self):
        taglib.tag("interface", "foo")
        r = self.roundtrip()
        eq_(len(r), 0)

    def test_single_used_tag(self):
        t = taglib.tag("interface", "foo")
        t.used(10, "myfile")

        r = self.roundtrip()
        eq_(r[0]["tag"], "interface--foo")

    def test_implies(self):
        p = taglib.tag("interface", "foo")
        s = taglib.tag("device", "goo")
        s.used(1, "myfile")
        p.implies(s, 2, "myfile")

        r = self.roundtrip()
        eq_(r[0]["tag"], "device--goo")
        eq_(r[0]["location"], "myfile:1")
        eq_(r[1]["tag"], "interface--foo")
        eq_(r[1]["implies"], "device--goo")
        eq_(r[1]["location"], "myfile:2")
        
    def test_implied_by(self):
        p = taglib.tag("interface", "foo")
        s = taglib.tag("device", "goo")
        p.used(1, "myfile")
        s.implied_by(p, 2, "myfile")

        r = self.roundtrip()
        eq_(r[0]["tag"], "interface--foo")
        eq_(r[0]["location"], "myfile:1")
        eq_(r[1]["tag"], "device--goo")
        eq_(r[1]["implied_by"], "interface--foo")
        eq_(r[1]["location"], "myfile:2")
        

class EnvironmentTagsTestCase(unittest.TestCase):

    def test_env_tags(self):
        import os
        os.environ["SESSION_ID"] = "testsession"
        os.environ["SESSION_DEVICE"] = "mydevice.example.com"
        os.environ["TRIGGER_KIND"] = "OS"
        os.environ["TRIGGER_NAME"] = "TESTOS"

        snapshot = taglib.env_tags.snapshot
        device = taglib.env_tags.device
        trigger = taglib.env_tags.trigger

        eq_(snapshot.qname, "snapshot--testsession")
        eq_(device.qname, "device--mydevice.example.com")
        eq_(trigger.qname, "OS--TESTOS")

        assert snapshot is taglib.env_tags.snapshot
        assert device is taglib.env_tags.device
        assert trigger is taglib.env_tags.trigger

