# ChessPlayer

Run python src/main.py

1. Build the Docker Image

Run this command in the directory containing your Dockerfile:

```
docker build -t chess-app .
```

This command builds the Docker image and tags it as chess-app.
2. Run the Docker Container

To run your application, use the following command:

```
docker run -it --rm --name running-app chess-app
```

This command runs your Python application inside the Docker container.

3. Running the Container for Interactive Development

Since you're still developing and debugging your code, you might want to run the container in a way that lets you execute main.py manually or run other commands. You can do this by overriding the default command:

```
docker run -it --rm --name running-app -v $(pwd)/src:/app/src chess-app bash
```

This command opens a bash shell inside your container, where you can manually run python src/main.py or other commands.
