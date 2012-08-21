# slosh - mini realtime web

slosh is the server component for a realtime data visualization project.  The
name is to show that I've actually heard of
[bosh](http://xmpp.org/extensions/xep-0124.html), but I needed something
sloppier.

# What it Does

slosh allows http clients to respond to events as they occur using long-polling
techniques.

Integration with existing services is quite easy.  Services simply POST json into a
topic URL and a GET on the same URL will return that json data with a few pieces of metadata.
**Note: if you use the MAILBOX type of topic (set in the tac file) the server will respond with a 404 error if you post to an inactive topic.
A topic is only active while someone is watching it (with a long-poll).
Once the user goes away the topic remains active for a configurable amount of time
before becoming inactive.  If you use the NORMAIL type of topic the topic exists as long as there is something watching it (with a long-poll) or data is being POST'ed to it

For example point your browser to http://localhost:8000/topics/test -- The
browser will hang indefinitely waiting for a results.  Now run the following:

    curl -d '{"response":{"message":[{"@id":"123","event":"Some Event Text"}]}}' http://localhost:8000/topics/test

You should instantly see results in your browser:

    {
        max: 1,
        saw: 1,
        res: [
            {
                response: {
                    message: [
                        {
                            @id: "123",
                            event: "Some Event Text"
                        }
                    ]
                }
            }
        ],
        delivering: 1
    }

If you repeat the above query three times and reload with the browser, you
should see queued results immediately:

    {
        max: 4,
        saw: 3,
        res: [
            {
                response: {
                    message: [
                        {
                            @id: "123",
                            event: "Some Event Text"
                        }
                    ]
                }
            },
            {
                response: {
                    message: [
                        {
                            @id: "123",
                            event: "Some Event Text"
                        }
                    ]
                }
            },
            {
                response: {
                    message: [
                        {
                            @id: "123",
                            event: "Some Event Text"
                        }
                    ]
                }
            }
        ],
        delivering: 3
    }

The `saw` value describes how many incoming messages were received by the
server.  It may be larger than the number of requests you receive if the rate
of incoming requests is higher than the rate at which you're processing the
results.

# Running

Copy `slosh.tac.sample` to `slosh.tac` and optionally edit for your
document root then use [twistd][twistd] to launch it.

To see the example app interactively on console, you can do the following:

    cp slosh.tac.sample slosh.tac
    twistd -ny slosh.tac

# Requirements

[twisted](http://twistedmatrix.com/) is required to do anything at all.

If you want JSON formatted results, the
[python-cjson](http://pypi.python.org/pypi/python-cjson) egg is required.


[twistd]: http://linux.die.net/man/1/twistd
