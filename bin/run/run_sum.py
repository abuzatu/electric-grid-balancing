"""Script to show how to run a sum."""

import utils.sum

class Sum:
    """Class to do Sum."""

    def __init__(self, do_test: bool) -> None:
        """Init."""
        self.do_test = do_test
        self._set_N()

    def _set_N(self) -> None:
        """Set N."""
        self.N = 2 if self.do_test else 10

    def run_all(self) -> None:
        """Run all."""
        sum = 0.0
        for i in range(self.N):
            sum+=utils.sum.my_sum(float(i), 10.0)
            print(f"i={i}, sum if i and 10 is {sum}")

if __name__ == "__main__":
    do_test = False
    Sum(do_test=do_test).run_all()