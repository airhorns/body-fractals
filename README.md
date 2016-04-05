This is a python program that renders 3D fractals and controls the parameters with a Kinect V2. Cool!

Example images:

![](http://i.giphy.com/3oGRFxnha4cVlWuutO.gif)
![](http://i.giphy.com/l4hLWTH8b9yLDPE1G.gif)
![](http://i.giphy.com/3oGRFg1KmJqdQUCn6w.gif)


### Running / browsing

The real thing is in the `prod` folder. To run:

```
$ pip install -r requirements.txt
$ git clone https://github.com/airhorns/vispy.git && cd vispy && git checkout bool-uniforms && pip install -e . && cd ..
$ git clone https://github.com/airhorns/primesense.git && cd primesense && pip install -e . && cd ..
$ python prod/main.py --fake
```

Checkout the bottom of `prod/main.py` for all the command line options.
