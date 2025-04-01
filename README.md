# NAND_Forensics

## oob_hunter.py

    This is a Python3 script to help in identifying potential OOB data of a NAND.

In some cases, the data on one's NAND may not align with the manufacturer's specifications for the chip. Here I will attempt to help identify potential OOB data if one is not confident of the layout of a particular NAND.

Using common NAND page sizes of `512`, `2048`, `4096`, and `8192` and their associated OOB sizes of `16`, `64`, `128`, and `256` (respectively), this script will analyze chunnks of the dump, scan for possible OOB offsets up to N pages forward, score and print the top candidate offsets in hex and decimal.

### Want better precision?
| SCAN_STEP | Pros | Cons |
| ------------ | ------------- | ------------ |
| `1`         | Meximum Precision (finds any offset) | Slower, especially with large `max_offset` and `sample_pages` |
| `4` | Very good balance (typical ECC is 4/8-byte aligned) | May skip rare misaligned layouts |
| `16` or `64` | Much faster for a quick triage | May miss good candidates between checks |

#### Recommendation
* Use `SCAN_STEP = 4` for most forensic work.
* Drop to `SCAN_STEP = 1` if you're not finding anything consistent, or you're analyzing a dump from a tool or chip with strange behavior.
* Increate it (i.e., `16` or `32`) if you want to attempt to narrow things down quickly and will do a second pass later.

### Scoring
    To evaluate potential OOB I score based on the following:
| Metric | What it means | What's common in real OOB |
| ------ | ------------- | ------------------------- |
| Entropy | Randomness / unpredictability | **Low to Medium** - ECC or metadata are structured |
| 0xFF ratio | Fraction of bytes that are `0xFF` | **High** - unused OOB is often padded with `0xFF` |
| Score | A combination heuristic `(1 - entropy/8) + 0xFF` ratio | **High Score** means low entropy + high 0xFF |

So, highly likely OOB means:
* **Low to medium entropy** (structured, like ECC)
* **High 0xFF ratio** (common padding in OOB space)
* **High score** (combined metric, favors both traits)

### Rule of thumb for interpreting script output 


``Offset 2112 (0x0840) | Entropy: 1.25 | FF Ratio: 0.85 | Score: 1.60`` **Very likely**

``Offset 2048 (0x0800) | Entropy: 5.81 | FF Ratio: 0.30 | Score: 0.56 ``**Unlikely**

``Offset 4160 (0x1040) | Entropy: 3.10 | FF Ratio: 0.70 | Score: 1.27 ``**Maybe**

* An **entropy below ~ 2.5** is usually *very* promising.
* An **0xFF ratio above ~0.7** is common for OOB.
* **Scores above 1.4** are often very solid hits.

### FAQ
#### Why does it take so long (relatively speaking) to evaluate when page size is 8192?

Layouts of 8192 are slower because:
* A `PAGE_SIZE` of `8192`, and a `SAMPLE_PAGES` of `1000` is ~ *MB scanned per test.  That's really not bad.
* But, with `SCAN_STEP = 4`, that's:
  * `8192 / 4 = 2048 offset chunks` 
  * For each of the `1000` pages that's **2 million OOB blocks processed**
  * Multiple that by 4 layouts and that's **8 million evaluations total!**

#### How can I speed up the script?
* Reduce `SAMPLE_PAGES`
  * You probably don't need 1000 pages to detect a repeating structure.
  * 300 pages will usually give reliable patterns.
* Temporarily increase `SCAN_STEP`
  * To quickly narrow it down, bump it up to `SCAN_STEP = 8` or even `16`.
  * Then, once you have a promissing page+OOB combo, **re-run just that one** with `SCAN_STEP = 1` to refine.
* Limit the scan to one layout
  * If you're mostly interested in one layout, (for example: 2048+64), comment out the others temporarily.
