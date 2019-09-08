# pyjobserver (**Work in Progress**)
A template to microservice-ify your sketchy Python code


## Background and Rationale

Many data science teams like working in Python for its ease and power in data exploration and modelling; but:

1. Python is a sloooow language to execute, and
1. Usually the more cutting edge your techniques, the further from production quality your data scientists' code gets

This leads to a common disconnect I'd characterise as "The DevOps Problem of Data Science": Just as developers in the bad old days didn't take responsibility for environment and operations management, many data science teams struggle when it comes to the productionisation of their models.

The natures and consequences of the software and data science DevOps problems are really similar: when the person creating algorithms isn't aware or involved enough in their route-to-live; unexpected risks, costs, or delays arise from either un-noticed impracticalities in the developed software, or mis-communications between the creators and the deliverers/maintainers.

Modern DevOps practices were enabled by **empowering tooling**: Technologies like build monitoring, automation and containerized/orchestrated deployment are _helping_ developers take on more responsibility for operations, by making it easy enough that doing so isn't a **drain on their productivity**.

The Data Science DevOps Problem will be solved the same way but is arguably harder: The gap to "this system runs fast and securely" is wider from "this maths solves the problem well" than it was from "this software runs fine on my machine".

For teams that are happy to take on model architecture constraints, there are already a variety of tools out there from major cloud providers that tackle ML model productionisation by offering robust runtimes for particular model types.

This repo aims a step below: to provide a Python micro-service skeleton app with guidelines to support data scientists dropping their own (potentially long-running) jobs. It's not as sophisticated or efficient as a fully optimised implementation of a particular model architecture as-a-service, but intended to support teams taking the first steps towards servicifying highly custom Python code.


## Design

Your target code is (or can be easily factored in to) a **Job**, which:

* Runs in an server configuration context (e.g. you can access secrets/etc via configuration loaded on server start, if needed)
* Takes an input **Spec** object, describing the data and parameters to be operated on
* Produces an output **Result**, including all required output data
* May optionally raise `error`s, `warning`s, `info` and `progress` ETA updates, or `critical` failures to abort execution
* Might take a long time and/or a lot of resources to run

`pyjobserver` should implement:

* A secure skeleton web-server with authentication capabilities, to protect your compute resources from abuse
* Support for multiple Job types with different handlers, to scale your resources efficiently
* Constraints on Job execution in case things go awry (e.g. time-outs, limited number of parallel tasks)

The usage sequence should go as follows:

* Server start-up includes configuration of job types, resource constraints, etc
* `POST` a Job Spec (including job type ID) to `/api/` to request processing of a job, which will return HTTP200 and the **Job ID** if successful (job accepted), or else a sensible HTTP error
* `GET` the status of your job from `/api/{Job ID}` which will return the result data, if ready... or better yet
* Connect to the **WebSocket stream** of updates at `/api/{Job ID}/ws` to receive live updates on progress/completion/errors without having to poll.

Job ID is a (Python UUID4) GUID and is the only information required (besides the overall API username and password) to request or connect to job updates: I.e. Jobs are not authenticated privately but are functionally private unless the Job ID GUID is intercepted or shared.

Job results/statuses/errors will be retained in the server in an expiring cache with a maximum length (i.e. until either the time-to-live expires or the cache becomes filled with new jobs). This ensures that even instantly completed jobs (before the client re-connects to poll status endpoint or webhook) are visible.

Attempting to access the status or WebSocket of a job no longer in cache should yield HTTP 404.


## Technical Implementation

Python 3.7^ is chosen for reasons including:

* Mature async support - which can provide more resource-efficient scaling (and fewer thread safety headaches) than threadpooling/etc.
* Typing annotations support - which can make the interface between Jobs and the Job Runner more concise

aiohttp is used as the basis of the webserver due to its async-native architecture and built-in support for WebSockets and client-side connections from one library: Many data science jobs may need to call external web services, which may help Job implementors keep to a common interface.
