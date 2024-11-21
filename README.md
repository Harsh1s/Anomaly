# Streaming Anomaly Detection

This server makes use of web-sockets to stream data from a client to a server and to perform real time anomaly detection on the data. 

## Installation

To install the application, you need to create a new virtual environment (or conda environment) and install the dependencies using the following commands:

```bash
pip install -r requirements.txt
```

Then you can seed the demo data, and start both the server and mock clients using the Makefile command: `make start`. The server would start at the URL [`http://localhost:3000/`](http://localhost:3000/) and would serve static pages that can be accessed via the browser.


## Components

The various components of the the application are as follows:

### Server

- We make use of a [FastAPI](https://fastapi.tiangolo.com/) server to handle web-socket as well as HTTP requests.
- Any client can connect to the web-socket server by identifying itself with a `client_id` and a `window` size (which is the number of previous data points that must be used to detect anomalies).
- After the same, the client can stream data to the server in the form of a JSON object with `timestamp` and `value` keys. The server will then perform anomaly detection on the data and return the result to the client (an object with `timestamp` and `anomaly` keys).
- The server also stores all the data points that it receives in a SQLite database for persistence and maintains the state of the client as active or not active.
- The server also serves the following webpages:
  - On the root URL, a page that displays the IDs of all the active clients.
  - On the `/client/{client_id}` URL, a page that displays the data points that the client has streamed to the server and the anomalies detected by the server. 
  
  These pages are rendered in real time, so you can just refresh the page to see the latest data.


### Client

- The client is a simple class that reads data from a CSV file and streams it to the server using a web-socket connection. 
- The client also stores all the messages sent and recieve in the `logs` directory for debugging purposes.

### Anomaly Detection

We currently make use of an ensemble of multiple models to detect anomalies in the data. We use simple majority voting to determine if a data point is an anomaly or not. 

The statistical models that we use are:

- [Z Score](https://en.wikipedia.org/wiki/Standard_score)
- [IQR](https://en.wikipedia.org/wiki/Interquartile_range)
- [EWMA](https://en.wikipedia.org/wiki/EWMA_chart)
- [Moving Average](https://en.wikipedia.org/wiki/Moving_average)
- [Isolation Forest](https://en.wikipedia.org/wiki/Isolation_Forest)

### Data Source

We also make use of `yfinance` to source stock data for the client to stream to the server.

### Demo Video

https://github.com/user-attachments/assets/cf94a20e-b3b2-44b5-89db-d0cd735a9fa5




