# UD-GreekCheck
Language-specific validation for Ancient Greek in UD

```
$ cat genesis.conllu | PYTHONPATH="/home/daniel/UD-GreekCheck:$PYTHONPATH" udapy -s .GreekCheck >/dev/null
[...]
2023-07-19 15:59:17,494 [WARNING] after_process_document - ud.MarkBugs Error Overview:
      unsplit-crasis          2
        finverb-mood         17
         no-PronType        163
       finverb-tense        167
          no-NumType        277
           no-Aspect        770
               TOTAL       1396
```

This has the same interface as the udapi MarkBugs module, and the structure is largely copied from there.

This mostly skips checks performed by MarkBugs or the standard validation process in favor of things not checked elsewhere.
