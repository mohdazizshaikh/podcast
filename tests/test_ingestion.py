import io
import json
import socket
import zipfile
import pytest
from podcast_gpt import ingestion as ing, projects, episode_plan as ep, source, cli


def req(kind):
    return {"topic":"Science","language":"Hindi","duration_minutes":1,"presenters":["Solo"],
            "video_format":"square","workflow":"manual","input_kind":kind,"research_mode":"knowledge"}


def test_text_evidence_binding_and_no_overwrite(tmp_path,monkeypatch):
    root=tmp_path/"private"
    p=tmp_path/"input.txt";p.write_text("Original source facts.\nSecond line.",encoding="utf-8")
    pid=projects.create(root,req("document"))["project_id"]
    with pytest.raises(ValueError,match="Import source"):projects.generate_outline(root,pid)
    imported=projects.import_source(root,pid,path=p)
    assert imported["stage"]=="source_imported"
    assert projects.inspect(root,pid)["stage"]=="source_imported"
    with pytest.raises(ValueError,match="overwritten"):projects.import_source(root,pid,path=p)
    def plan(data,*,evidence,**opts):
        assert evidence["text"]=="Original source facts.\nSecond line."
        return {"provider":"ollama","result":{"title":"Science","sections":[{"heading":"Intro","minutes":1,"summary":"Facts","presenters":["Solo"]}]}}
    monkeypatch.setattr(ep,"plan",plan)
    assert projects.generate_outline(root,pid)["stage"]=="outline_saved"
    assert projects.inspect(root,pid)["stage"]=="outline_saved"
    dest=projects.project(root,pid)/projects.EVIDENCE
    value=source.read_json(dest)
    value["evidence"]["text"]="changed"
    dest.write_text(json.dumps(value),encoding="utf-8")
    with pytest.raises(ValueError,match="hash"):projects.inspect(root,pid)


def test_docx_and_custom_script(tmp_path):
    p=tmp_path/"sample.docx"
    with zipfile.ZipFile(p,"w") as z:
        z.writestr("word/document.xml",'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Hello</w:t></w:r></w:p><w:p><w:r><w:t>World</w:t></w:r></w:p></w:body></w:document>')
    assert ing.extract("document",path=p)["text"]=="Hello\nWorld"
    script=tmp_path/"script.md";script.write_text("Solo: नमस्ते\nSolo: धन्यवाद",encoding="utf-8")
    assert ing.extract("custom_script",path=script)["text"]=="Solo: नमस्ते\nSolo: धन्यवाद"
    script.write_text("x"*(ing.MAX_TEXT+1),encoding="utf-8")
    with pytest.raises(ValueError,match="no silent truncation"):ing.extract("custom_script",path=script)


def test_pdf_text_fixture(tmp_path):
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
    writer=PdfWriter();page=writer.add_blank_page(width=300,height=200)
    font=DictionaryObject({NameObject("/Type"):NameObject("/Font"),NameObject("/Subtype"):NameObject("/Type1"),NameObject("/BaseFont"):NameObject("/Helvetica")})
    page[NameObject("/Resources")]=DictionaryObject({NameObject("/Font"):DictionaryObject({NameObject("/F1"):writer._add_object(font)})})
    stream=DecodedStreamObject();stream.set_data(b"BT /F1 12 Tf 20 100 Td (Source facts) Tj ET")
    page[NameObject("/Contents")]=writer._add_object(stream)
    path=tmp_path/"sample.pdf"
    with path.open("wb") as handle:writer.write(handle)
    assert ing.extract("pdf",path=path)["text"]=="Source facts"


def test_url_consent_and_public_target_without_network():
    def never(url):raise AssertionError("No fetch before consent")
    with pytest.raises(ValueError,match="explicit"):ing.extract("url",url="https://example.com",fetcher=never)
    def fetch(url):return b"<html><head><title>Hidden</title></head><body><p>Facts</p><script>evil()</script><p>More</p></body></html>","text/html","utf-8"
    assert ing.extract("url",url="https://example.com/article",allow_web_fetch=True,fetcher=fetch)["text"]=="Facts\nMore"
    def resolve(*a,**kw):return [(socket.AF_INET,socket.SOCK_STREAM,6,"",("93.184.216.34",443))]
    assert ing._target("https://example.com/article",resolve)==("example.com","/article","93.184.216.34")
    for url in ("http://example.com","https://example.com:123/","https://user@example.com/","https://example.com/?token=secret"):
        with pytest.raises(ValueError):ing._target(url,resolve)
    def private(*a,**kw):return [(socket.AF_INET,socket.SOCK_STREAM,6,"",("127.0.0.1",443))]
    with pytest.raises(ValueError,match="Private"):ing._target("https://example.com",private)


def test_cli_import_source(tmp_path):
    root=tmp_path/"studio";p=tmp_path/"script.txt";p.write_text("Solo: Hello",encoding="utf-8")
    pid=projects.create(root,req("custom_script"))["project_id"]
    args=cli.parse(["--workspace",str(root),"project-import-source","--project-id",pid,"--file",str(p)])
    assert cli.execute(args)["stage"]=="source_imported"
