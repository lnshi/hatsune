## Description

- This is a heterogeneous cluster job scheduling/management system written in Python 3.5.1.

- Mainly aims at making Windows nodes can work together with others Linux/Unix nodes in a same cluster.

## Architecture

- <img src="hatsune.png"/>

## How to setup development/testing environment

1. Install and setup Python 3.5.1 properly.

2. Create subfolder `hatsune` in directory '/var/run/', and **change the owner of directory '/var/run/hatsune' to your current user (need root privilege for this operations) with `sudo chown CURRENT_USER /var/run/hatsune`**, for server creating and storing the `pid file` and `pipe files`; This is an one-off task.

3. In bottom of this source code file: [hatsune/server/hatsune.py](https://github.com/lnshi/hatsune/blob/master/server/hatsune.py), use the **_hatsune.run()** instead of **_hatsune.start()** for running server in foreground for testing purpose, then you can see the print message easily.

4. One terminal for `python server/hatsune.py` (server daemon), one for `python server/console.py` (console daemon), and the other one for `python computing/computing.py` (computing daemon), then having fun to proceed your development and testing.

## Accumulations / References

**1. I/O Model: select, poll, epoll(kqueue on OS X)**

**2. Python threading vs multiprocessing vs asyncio**

  - For 'threading', threads will not actually run concurrently due to Python's Global Interpreter Lock (GIL), that means even in Multi-core CPU, at the exactly particular time, always only one core is taken.

  - http://stackoverflow.com/questions/3044580/multiprocessing-vs-threading-python

  - http://stackoverflow.com/questions/4496680/python-threads-all-executing-on-a-single-core

  - Differences among these three approaches refer to this video: https://youtu.be/B0Qfe3U_hKU

  - Generally:

    1. Analyse your task(CPU-Bound, I/O-Bound), then decide how to parallelize.

    2. 'threading' module doesn't really takes the Multi-core advantages.

    3. 'multiprocessing' do take the Multi-core advantages but all processes hold their own memory, you need to deal with the interaction between different processes and the variables synchronisation properly.

**3. How to use Python's low-level networking interface - socket**

  - http://stackoverflow.com/questions/1708835/receiving-socket-python

    1. The network is always unpredictable. TCP makes a lot of this random behaviour go away for you. One wonderful thing TCP does: it guarantees that the bytes will arrive in the same order. But! It does not guarantee that they will arrive chopped up in the same way. You simply cannot assume that every send() from one end of the connection will result in exactly one recv() on the far end with exactly the same number of bytes.

    2. When you say socket.recv(x), you're saying 'don't return until you've read x bytes from the socket'. This is called "blocking I/O": you will block (wait) until your request has been filled. If every message in your protocol was exactly 1024 bytes, calling socket.recv(1024) would work great. But it sounds like that's not true. If your messages are a fixed number of bytes, just pass that number in to socket.recv() and you're done.

    3. But what if your messages can be of different lengths? Now you have a new problem: how do you know when the sender has sent you a complete message? The answer is: you don't. You're going to have to make the length of the message an explicit part of your protocol. Here's the best way: prefix every message with a length, either as a fixed-size integer (converted to network byte order using socket.ntohs() or socket.ntohl() please!) or as a string followed by some delimiter (like '123:'). This second approach is often less efficient.

  - http://stackoverflow.com/questions/17667903/python-socket-receive-large-amount-of-data

    1. TCP/IP is a stream-based protocol, not a message-based protocol. There's no guarantee that every send() call by one peer results in a single recv() call by the other peer receiving the exact data sent—it might receive the data piece-meal, split across multiple recv() calls, due to packet fragmentation.

    2. You need to define your own message-based protocol on top of TCP in order to differentiate message boundaries. Then, to read a message, you continue to call recv() until you've read an entire message or an error occurs.

    3. One simple way of sending a message is to prefix each message with its length. Then to read a message, you first read the length, then you read that many bytes.

**4. Python's 'ATclassmethod' and 'ATstaticmethod' decorator**

  - http://stackoverflow.com/questions/136097/what-is-the-difference-between-staticmethod-and-classmethod-in-python

    ```
    class A(object):
    def foo(self,x):
        print "executing foo(%s,%s)"%(self,x)

    @classmethod
    def class_foo(cls,x):
        print "executing class_foo(%s,%s)"%(cls,x)

    @staticmethod
    def static_foo(x):
        print "executing static_foo(%s)"%x    

    a=A()
    ```

**5. Amend the most recent commit message in git**

  - http://stackoverflow.com/questions/179123/edit-an-incorrect-commit-message-in-git

  - Amending the most recent commit message

    1. git commit --amend -m "New commit message."

  - Changing the message of a commit that you've already pushed to your remote branch

    1. git commit --amend -m "New commit message."

    2. git push --force origin master

**6. Python how to pass a variable to method by reference?**

  - http://stackoverflow.com/questions/986006/how-do-i-pass-a-variable-by-reference

**7. For command line parsing, except the 'argparse' module, don't forget the 'shlex' module**

  - https://docs.python.org/3.5/library/subprocess.html

  - Note shlex.split() can be useful when determining the correct tokenization for args, especially in complex cases:

    ```
    >>> import shlex, subprocess
    
    >>> command_line = input()
    /bin/vikings -input eggs.txt -output "spam spam.txt" -cmd "echo '$MONEY'"
    >>> args = shlex.split(command_line)
    >>> print(args)
    ['/bin/vikings', '-input', 'eggs.txt', '-output', 'spam spam.txt', '-cmd', "echo '$MONEY'"]
    >>> p = subprocess.Popen(args) # Success!
    ```

**8. Understanding Python's 'with' statement**

  - http://effbot.org/zone/python-with-statement.htm


