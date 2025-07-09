# Here you can find test Book Management API.
Docker Compose will run FastAPI with Swagger, PostgreSQL, and also Tests.


> Running the scripts:

````
$ git clone https://github.com/sanarkk/book-management-system-api.git
````
````
$ cd book-management-system-api
````
````
Create a new .env file with provided example file.
````
````
docker-compose up --build -d
````
````
http://localhost:8001/docs
````

> Testing:
````
docker exec -it book-management-system-api /bin/sh
````
````
pytest
````




<sub>created by sanarkk</sub>
