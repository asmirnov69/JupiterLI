# JupiterLI

JupiterLI - named after small Jupiter moon [Jupiter LI](https://en.wikipedia.org/wiki/Jupiter_LI)

Real-time data visualization dashboard powered by ZeroMQ PUB/SUB and NiceGUI. Data producers publish on a ZeroMQ PUB socket; the browser dashboard subscribes to topics and updates live as new data arrives.

## Install JupiterLI

```bash
pip install git+https://github.com/asmirnov69/JupiterLI
```

`pyzmq` is pulled in as a dependency — no external broker process is needed.

## Run the example

In one terminal, start the data producer (publishes random values on topics `data1` / `data2` every ~0.25s, binds `tcp://*:5555`):
```bash
python examples/producer.py
```

In another terminal, start the dashboard:
```bash
jupiterli-backend examples/producer.ttl
```

Then open http://localhost:8080 in your browser.
