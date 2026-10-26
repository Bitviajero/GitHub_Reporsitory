def merge(L,R):
    out = []
    while L and R:
        if L[0] < R[0]:
            out.append(L.pop(0))
        else:
            out.append(R.pop(0))
    return out