import logging
import matplotlib.pyplot as plt


class DampedSpring():
    """
    A mass and spring system in one dimension with friction. The system
    oscillates and the amplitude of the oscillation decreases gradually due to
    the loss of energy (work of friction force). The rate of decrease of
    the amplitude is determined by the friction coefficient.

    Only the simplest form of the drag force (-kv) is used. In reality, one may
    consider terms of higher order. Alternatively, one might take the friction
    coefficient, k, as a function of velocity.

    Source:
    https://micropore.wordpress.com/2011/03/02/python-1d-mass-and-spring-system-with-friction
    """
    def __init__(self, dt=0.001, k=10, m=1, k1_drag=0.5, h0=0.5, v0=1.0):
        h0 = h0  # initial deviation from equilibrium (m)
        v0 = v0  # initial speed (m/s)
        self.dt = dt  # time step (s)

        self.k = k  # spring constant (N/m)
        self.m = m  # mass (kg)
        self.k1_drag = k1_drag  # drag (kg/s)
        # self.eta = 0.8  # v_in/v_out in an inelastic encounter

        self.h = h0  # height (m)
        self.v = v0  # velocity (m/s)
        self.a = 0  # acceleration (m/s^2)

        logging.info("Spring constant (k): {} dt: {}".
                     format(self.k, self.dt))

        self.K = 0  # kinetic energy (J)
        self.V = 0  # potential energy (J)
        self.E = 0  # total energy (J)
        self.calc_energy()
        # self.Energy = self.E
        self.calc_force()

    def calc_energy(self):
        self.K = self.m * pow(self.v, 2) / 2
        self.V = self.k * pow(self.h, 2) / 2
        self.E = self.K + self.V

    def calc_force(self):
        """
        Equations:
        F = dp/dt = -kx
        p = mv
        """
        self.a = -self.k / self.m * self.h - self.k1_drag / self.m * self.v
        self.v += self.a * self.dt
        self.h += self.v * self.dt
        # self.dE = -self.k1_drag * pow(self.v, 2) * self.dt
        # self.Energy += self.dE
        self.calc_energy()

        logging.debug("E_k: {} E_p: {}".
                      format(self.K, self.V))

    def bounce(self):
        """
        Calculate (one integration step) and return height

        :return: mass height
        """
        self.calc_force()
        return self.h


def run():
    t = 0
    dt = 0.01
    T = [0.]
    X = [0.]
    K = [0.]
    V = [0.]
    E = [0.]
    spring = DampedSpring(dt=dt)
    for i in range(int(10/dt)):
        T.append(t * dt)
        X.append(spring.bounce())
        K.append(spring.K)
        V.append(spring.V)
        E.append(spring.E)
        t += 1

    # remove t0 values
    T.pop(0)
    X.pop(0)
    K.pop(0)
    V.pop(0)
    E.pop(0)

    plt.figure()
    plt.axhline(0, color='black')
    plt.plot(T, X)
    plt.title("Damped spring")
    plt.legend(("Displacement",))
    plt.xlabel("Time (s)")
    plt.ylabel("Displacement (m)")

    plt.figure()
    plt.plot(T, K)
    plt.plot(T, V)
    plt.plot(T, E)
    plt.title("Damped spring")
    plt.legend(("Kinetic", "Potential", "Total",))
    plt.xlabel("Time (s)")
    plt.ylabel("Energy (J)")
    plt.show()


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)
    run()
