import unittest

import numpy as np

from openmdao.api import Problem, ExplicitComponent, Group, IndepVarComp
from openmdao.jacobians.assembled_jacobian import DenseJacobian
from openmdao.test_suite.components.double_sellar import DoubleSellar
from openmdao.test_suite.components.paraboloid import Paraboloid
from openmdao.test_suite.components.sellar_feature import SellarNoDerivativesCS
from openmdao.utils.assert_utils import assert_check_partials, assert_no_approx_partials, assert_no_dict_jacobians


class TestAssertUtils(unittest.TestCase):

    def test_assert_check_partials_no_exception_expected(self):
        import numpy as np
        from openmdao.api import Problem, ExplicitComponent
        from openmdao.utils.assert_utils import assert_check_partials

        class MyComp(ExplicitComponent):
            def setup(self):
                self.add_input('x1', 3.0)
                self.add_input('x2', 5.0)

                self.add_output('y', 5.5)

                self.declare_partials(of='*', wrt='*')

            def compute(self, inputs, outputs):
                """ Doesn't do much. """
                outputs['y'] = 3.0 * inputs['x1'] + 4.0 * inputs['x2']

            def compute_partials(self, inputs,     partials):
                """Correct derivative."""
                J = partials
                J['y', 'x1'] = np.array([3.0])
                J['y', 'x2'] = np.array([4.0])

        prob = Problem()
        prob.model = MyComp()

        prob.set_solver_print(level=0)
        prob.setup(check=False)
        prob.run_model()

        data = prob.check_partials(suppress_output=True)
        atol = 1.e-6
        rtol = 1.e-6
        assert_check_partials(data, atol, rtol)

    def test_assert_check_partials_exception_expected(self):
        class MyComp(ExplicitComponent):
            def setup(self):
                self.add_input('x1', 3.0)
                self.add_input('x2', 5.0)

                self.add_output('y', 5.5)

                self.declare_partials(of='*', wrt='*')

            def compute(self, inputs, outputs):
                """ Doesn't do much. """
                outputs['y'] = 3.0 * inputs['x1'] + 4.0 * inputs['x2']

            def compute_partials(self, inputs, partials):
                """Intentionally incorrect derivative."""
                J = partials
                J['y', 'x1'] = np.array([4.0])
                J['y', 'x2'] = np.array([40])

        prob = Problem()
        prob.model = MyComp()

        prob.set_solver_print(level=0)

        prob.setup(check=False)
        prob.run_model()

        data = prob.check_partials(suppress_output=True)

        atol = 1.e-6
        rtol = 1.e-6
        try:
            assert_check_partials(data, atol, rtol)
        except AssertionError as err:
            expected_str = "error in partial of y wrt x1 in"
            self.assertTrue(expected_str in str(err),
                            msg="\n\nActual err msg:\n{} \n\ndoes not contain expected string:\n\n{}".format(str(err),
                                                                                                     expected_str))
        else:
            self.fail('Exception expected.')

    def test_assert_no_approx_partials_exception_expected(self):

        prob = Problem()
        prob.model = SellarNoDerivativesCS()

        prob.setup(check=False)

        try:
            assert_no_approx_partials(prob.model, include_self=True, recurse=True)

        except AssertionError as err:
            expected_err = \
'''The following components use approximated partials:
    cycle.d1
        of=*               wrt=*               method=cs
    cycle.d2
        of=*               wrt=*               method=cs
'''
            self.assertEqual(str(err), expected_err)
        else:
            self.fail('Exception expected.')

    def test_assert_no_approx_partials_exception_not_expected(self):

        prob = Problem()
        prob.model = DoubleSellar()

        prob.setup(check=False)

        assert_no_approx_partials(prob.model, include_self=True, recurse=True)

    def test_assert_no_dict_jacobians_exception_expected(self):

        prob = Problem()
        prob.model = SellarNoDerivativesCS()

        prob.setup(check=False)

        try:
            assert_no_dict_jacobians(prob.model, include_self=True, recurse=True)

        except AssertionError as err:
            expected_err = \
'''The following groups use dictionary jacobians:
    
    cycle'''
            self.assertEqual(str(err), expected_err)
        else:
            self.fail('Exception expected.')

    def test_assert_no_dict_jacobians_exception_not_expected(self):

        model = Group()
        ivc = IndepVarComp()
        ivc.add_output('x', 3.0)
        ivc.add_output('y', -4.0)
        model.add_subsystem('des_vars', ivc)
        model.add_subsystem('parab_comp', Paraboloid())

        model.connect('des_vars.x', 'parab_comp.x')
        model.connect('des_vars.y', 'parab_comp.y')

        prob = Problem(model)
        prob.model.jacobian = DenseJacobian()

        prob.setup(check=False)

        assert_no_dict_jacobians(prob.model, include_self=True, recurse=True)
