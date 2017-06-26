
def test_fetch_stacks():
    import gcns
    g=gcns.MergedGCNCircSource(["GW170104","GW150914","170105A"])

    gcn=g.gcn_circ[1]

    print(gcn.gcn_data)
    #print(gcn.reduced_content)

    print(gcn.render_bib())

    g.write_bib("./test.bib")