"""Six-cell illustration; repeated eigenvalues make individual bases nonunique."""
import numpy as np
from .build_modes import power75


def build_toy_w(epsilon=0.):
    w = np.zeros((6, 6))
    w[1, 0] = w[2, 1] = w[0, 2] = -1.
    w[4, 3] = w[5, 4] = w[3, 5] = -1.
    w[3, 0] = w[0, 3] = epsilon
    return w


def main():
    for epsilon in [0., .05]:
        values, vectors = np.linalg.eig(build_toy_w(epsilon))
        print(f"coupling={epsilon}")
        for i in np.argsort(-abs(values)):
            print(f"lambda={values[i]} support={power75(vectors[:, i]).tolist()}")
    print("Identical uncoupled loops have repeated eigenvalues: localized basis vectors are not unique.")


if __name__ == "__main__":
    main()
