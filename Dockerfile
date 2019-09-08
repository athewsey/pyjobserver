FROM python:3.7-buster

# Use poetry to manage dependencies on a python/Debian image base

RUN apt-get update && apt-get upgrade -y

# Install Poetry:
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
# Enable Poetry in same session:
ENV PATH="${PATH}:/root/.poetry/bin"
RUN export PATH

ENV PORT 4000
EXPOSE 4000
COPY . /home/python/app/
WORKDIR /home/python/app

RUN poetry install

CMD ["poetry", "run", "python", "-m", "pyjobserver"]
