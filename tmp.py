import sys
import numpy as np

def main():
    a = np.loadtxt("mobility_dataset.csv", delimiter=',', skiprows=1)
    print(np.shape(a))

if __name__=="__main__":
    main()