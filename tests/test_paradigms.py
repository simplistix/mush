from testfixtures import ShouldRaise
from testfixtures.mock import Mock

from mush.paradigms import Paradigms


class TestCollection:

    def test_register_not_importable(self):
        p = Paradigms()
        obj = p.register_if_possible('mush.badname', 'ParadigmClass')

        with ShouldRaise(ModuleNotFoundError("No module named 'mush.badname'")):
            obj.claim(lambda: None)

        with ShouldRaise(ModuleNotFoundError("No module named 'mush.badname'")):
            obj.process((o for o in []))

    def test_register_class_missing(self):
        p = Paradigms()
        with ShouldRaise(AttributeError(
                "module 'mush.paradigms.normal_' has no attribute 'BadName'"
        )):
            p.register_if_possible('mush.paradigms.normal_', 'BadName')

    def test_shifter_not_importable(self):
        p1 = Mock()
        p2 = Mock()
        p = Paradigms()
        p.register(p1)
        p.add_shifter_if_possible(p1, p2, 'mush.badname', 'shifter')

        caller = p.find_caller(lambda: None, target_paradigm=p2)
        with ShouldRaise(ModuleNotFoundError("No module named 'mush.badname'")):
            caller()
            
    def test_shifter_callable_missing(self):
        p = Paradigms()
        with ShouldRaise(AttributeError(
                "module 'mush.paradigms.normal_' has no attribute 'bad_name'"
        )):
            p.add_shifter_if_possible(Mock(), Mock(), 'mush.paradigms.normal_', 'bad_name')

    def test_find_paradigm(self):
        p1 = Mock()
        p2 = Mock()
        p = Paradigms()
        p.register(p1)
        p.register(p2)

        assert p.find_paradigm(lambda: None) is p2

        p2.claim.return_value = False

        assert p.find_paradigm(lambda: None) is p1

    def test_no_paradigm_claimed(self):
        p_ = Mock()
        p_.claim.return_value = False
        p = Paradigms()
        p.register(p_)
        with ShouldRaise(Exception('No paradigm')):
            p.find_paradigm(lambda: None)
