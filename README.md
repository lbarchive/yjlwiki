GAE Wiki
========

This is a simple wiki engine for Google App Engine.

I [cloned][clone] original [GAEWiki][], but push to Bitbucket, because the clones on Google Code can not have Downloads/Wiki/Issues tabs.

[clone]: http://code.google.com/r/livibetter-yjlwiki/
[GAEWiki]: http://code.google.com/p/gaewiki/

Installation
------------

1. Create a new Google App Engine.
2. Copy `sample-app.yaml` to be `app.yaml` and replace `<YOUR GAE ID>` with your ID.


Changes
-------

I only made some changes when I felt needed, here is a short list:

* Python 2.7 / Django 1.2.
* gae-pytz with pytz-2012h.
* Markdown 2.2.1
* Use Markdown wikilinks extension to handle internal wiki link:

  * Temporarily disabled: `List`, `ListChildren`, `gaewiki:mp3player`, `gaewiki:map`, `Image`.


Contributors
------------

See AUTHORS


License
-------

The wiki itself is distributed under GNU GPL v3.

pytz is distributed under the MIT license.
