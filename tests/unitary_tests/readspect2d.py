import brukerIO
import numpy
def showser(fid2D):
    import matplotlib.pyplot as p
    fig, ax = p.subplots()
    ax.set_xlabel("F2/points")
    ax.set_ylabel("F1/points")
    ax.set_xlim(0,fid2D.shape[-1])
    ax.set_ylim(0,fid2D.shape[0])
    ax.contour(fid2D, levels=[i*fid2D.max() for i in numpy.arange(0.03, 1.0, 0.1)])

    p.show()

# manage arguments
import argparse
parser = argparse.ArgumentParser(description='Read processed spectrum file')
parser.add_argument('infile', help='Full path of the dataset to process')

args = parser.parse_args()
dat = brukerIO.dataset(brukerIO.splitprocpath(args.infile))
spect2D = dat.readspect2d()
showser(spect2D)

