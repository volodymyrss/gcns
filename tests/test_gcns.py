
def test_ligo_fetch():
    import gcns
    g=gcns.LIGOGCNCircSource(["GW170104","GW150914"])

    gcn=g.gcn_circ[1]

    print(gcn.gcn_data)
    #print(gcn.reduced_content)

    print(gcn.render_bib())

    g.write_bib("./test.bib")