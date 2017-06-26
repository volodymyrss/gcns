import requests
import requests_cache
import re
import os
import jinja2
import datetime as dt

requests_cache.install_cache('cache')

class GCNCirc:
    def __init__(self,content):
        self.parse(content)

    def extract_fields(self, content):
        self.gcn_data = {}

        self.reduced_content = re.sub("^/+\n","",content)
        for gcn_field in ["TITLE", "NUMBER", "SUBJECT", "DATE", "FROM"]:
            regex = re.compile(gcn_field + ":(.*?)\\n")
            self.gcn_data[gcn_field] = re.search(regex, content).group(1).strip()
            self.reduced_content = re.sub(regex, "", self.reduced_content)

        self.date=dt.datetime.strptime(self.gcn_data['DATE'],"%y/%m/%d %H:%M:%S GMT")
        self.gcn_data['YEAR']=self.date.strftime("%Y")

        return self.gcn_data, self.reduced_content

    def extract_authors(self):
        #self.authors=
        self.authors_paragraph=re.search(".*?(?=\\n\\n)",self.reduced_content,re.S | re.M).group(0).replace("\n","")
        self.authors_paragraph=self.authors_paragraph.replace(" and ",", ")
        self.authors_paragraph = re.sub("\(.*?\)","",self.authors_paragraph)
        self.authors_paragraph = re.sub("\+", " ", self.authors_paragraph)

        self.authors_paragraph=self.authors_paragraph.replace("C.-C., Ngeow","C.-C. Ngeow ") # put in known bugs

        self.authors=[]

        first_then_last=True

        delimiter = ","
        if len(self.authors_paragraph.split(";"))>3:
            delimiter=";"
            first_then_last=False

        for author_line in self.authors_paragraph.split(delimiter):
            author_line=author_line.strip()

            if author_line=="": continue
            if re.match("\(.*?\)",author_line): continue
            if 'University' in author_line: continue
            if 'Russia' in author_line: continue
            if 'group' in author_line: continue
            if 'report' in author_line: continue

            print("author line:", author_line)

            r = re.search("(.*?)\((.*?)\)?", author_line)
            #r = re.findall("(.*?)(\(.*?\))?(?=[,\\n])", author)
            if r is not None:
                author_line=r.group(1).strip() # discard institute here

            author_line = re.sub("([a-z])([A-Z])","\\1 \\2",author_line)
            author_line = re.sub("([A-Z]).([A-Z])", "\\1 \\2", author_line)

            if first_then_last:
                fn,ln=re.search("(.*) (.*)",author_line).groups()
            else:
                ln, fn = re.search("(.*),(.*)", author_line).groups()

            self.authors.append(dict(firstname=fn,lastname=ln))

            print(dict(firstname=fn,lastname=ln))


    def parse(self, content):
        self.extract_fields(content)
        self.extract_authors()

        return self.gcn_data, self.reduced_content

    def __repr__(self):
        return "["+self.__class__.__name__+" "+self.gcn_data['NUMBER']+"]"

    def render_bib(self):
        if len(self.authors)==0:
            return ""

        latex_jinja_env = jinja2.Environment(
            block_start_string='\BLOCK{',
            block_end_string='}',
            variable_start_string='\VAR{',
            variable_end_string='}',
            comment_start_string='\#{',
            comment_end_string='}',
            line_statement_prefix='%%\LINE',
            line_comment_prefix='%#',
            trim_blocks=True,
            autoescape=False,
            loader=jinja2.FileSystemLoader(os.path.abspath('../')),
            undefined=jinja2.StrictUndefined,
        )

        context=self.gcn_data

        context['authors']=self.authors

        return latex_jinja_env.get_template("gcn_reference.bib.tpl").render(context)

class GCNCircSource:
    def __init__(self):
        pass

    def preload(self):
        pass

    def write_bib(self,fn):
        with open(fn,"wt") as f:
            for gcn in self.gcn_circ:
                f.write("\n\n"+gcn.render_bib()+"\n\n")

class StandardGCNCircSource(GCNCircSource):
    pass


class LIGOGCNCircSource(GCNCircSource):
    def __init__(self,ligo_triggers):
        self.ligo_triggers=ligo_triggers

        self.preload()

    def split_gcn_stack(self,gcn_stack):
        r = re.findall("/{5,}\\n.*?(?=/{5,})", gcn_stack, re.MULTILINE | re.S)
        print("found %i gcns"%len(r))
        return r


    def preload(self):
        self.gcn_circ=[]

        for ligo_trigger in self.ligo_triggers:
            gcn_stack=requests.get("https://gcn.gsfc.nasa.gov/other/%s.gcn3" % ligo_trigger).content.decode('utf-8',errors='ignore')
            for gcn_content in self.split_gcn_stack(gcn_stack):
                gcn=GCNCirc(gcn_content)
                print(gcn)
                self.gcn_circ.append(gcn)

