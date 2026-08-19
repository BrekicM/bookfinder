# Serbian Cyrillic is transliterated from Serbian Latin, not maintained separately

Serbian Latin and Serbian Cyrillic are one language in two alphabets — every word maps letter-for-letter (accounting for digraphs like lj/nj/dž), with no ambiguity going Latin→Cyrillic. Maintaining two hand-written translation sets would mean every string change has to be made twice, with no way to catch drift between them. Instead, only Serbian (Latin) is authored by hand; Serbian (Cyrillic) is produced by mechanical transliteration at render time, guaranteeing the two scripts can never disagree.
