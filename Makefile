reset:
	rm -rf __pycache__/ data/ logs/
	rm -rf timeseries.db
	python generate_data.py

start:
	make reset

	python server.py &
	sleep 10 

	python client.py
