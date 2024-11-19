## MD5.01

**Category**: Crypto, Misc

**Author**: rbtree

**Description**: Wow, MD5 is vulnerable! Check this paper: https://eprint.iacr.org/2004/199.pdf.

**Public Files**: `dist/main.py`

**Solution**: Put those two values:

- `4b870eb51d754eacc9d36901e24dc0d1d6c75817a2d214bcd86e8159d433c59e902d538c483e4709d0984339847fd27ad962395ff20caffbd6c43e95a7301a86e8dfcfef2b51fa0b6b61b2f684f77c85afec701322d20fc12c3307862a91a5181131346305d02ffbdaf5f7cea99c525c0987125254e89fea44a382ad4543a096`
- `4b870eb51d754eacc9d46901e24dc0d1d6c75817a2d214bcd86e8159d433c59e902d538c483e4709d0984339847fd27ad962395ff20caffbd6c43e95a7301a86e8dfcfef2b51fa0b6b60b2f684f77c85afec701322d20fc12c3307862a91a5181131346305d02ffbdaf5f7cea99c525c0987125254e89fea44a382ad4543a096`

**Notes**:

- The answer pair is found by [Hashclash](https://github.com/cr-marcstevens/hashclash).
