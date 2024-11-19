## MD5.1

**Category**: Crypto

**Author**: rbtree

**Description**: Wow, MD5 is vulnerable! Check this paper: https://eprint.iacr.org/2010/643.pdf.

**Public Files**: `dist/main.py`

**Solution**: Run `priv/submit.py <HOST> <PORT>`. The answers are found with `priv/calc_*.py`.

**Notes**:

- The author's solution is based on these three papers: https://eprint.iacr.org/2013/170.pdf, https://eprint.iacr.org/2009/223.pdf, https://eprint.iacr.org/2008/391.pdf.

- Maybe it is still possible to solve with Hashclash, by providing the differential path given by the papers to it.
