# slosh - mini realtime web

slosh is the server component for a realtime data visualization project.  The
name is to show that I've actually heard of
[bosh](http://xmpp.org/extensions/xep-0124.html), but I needed something
sloppier.

# What it Does

slosh allows http clients to respond to events as they occur using long-polling
techniques.

Integration with existing services is quite easy.  Services simply POST into a
topic URL and a GET on the same URL will return that data in XML form.

For example point your browser to http://localhost:8000/test -- The browser
will hang indefinitely waiting for a results.  Now run the following:

    curl -d 'x=hello!' http://localhost:8000/test

You should instantly see results in your browser:

    <res>
      <p>
        <x>hello!</x>
      </p>
    </res>

If you repeat the above query three times and reload with the browser, you
should see queued results immediately:

    <res>
      <p>
        <x>hello!</x>
      </p>
      <p>
        <x>hello!</x>
      </p>
      <p>
        <x>hello!</x>
      </p>
    </res>
