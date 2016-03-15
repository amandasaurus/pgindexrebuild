<a name="v0.5.0"></a>
## v0.5.0 (2016-03-15)


#### Features

*   Use python logging framework to show log messages ([dec0f3c5](dec0f3c5))



<a name="v0.4.0"></a>
## v0.4.0 (2016-03-14)


#### Bug Fixes

*   Don't show 6  decimal places for percentages ([66f1c1e2](66f1c1e2))
*   size_pretty supports negative numbers ([2a01efe3](2a01efe3))
*   Only include things in public schema. ([6196512d](6196512d))
*   Remove objects with zero wasted space ([efd21026](efd21026))
*   Make -U/--user not be a required option ([0cd7f2a9](0cd7f2a9))

#### Features

*   Gracefully handle a previously interuppted job ([02095201](02095201))
*   Print out percentage wasted ([0b71052f](0b71052f))
*   Output for sizes uses pretty printing ([e6ea6f60](e6ea6f60))
*   Show how much disk space was saved each time & at end ([90f6e53e](90f6e53e))



<a name="v0.3.0"></a>
## v0.3.0 (2016-03-11)


#### Features

*   Reindex smaller tables first ([0563bb04](0563bb04))
*   Add -U/--user flag to change pg user ([0a3dd332](0a3dd332))
*   Add setup.py ([b8faab27](b8faab27))
*   Add --dry-run option ([ee8958c9](ee8958c9))

#### Bug Fixes

*   Correct printed output ([fc0445fc](fc0445fc))



<a name="v0.2.0"></a>
## v0.2.0 (2016-03-11)


#### Features

*   Exclude pg_catalog indexes ([39bdd7b3](39bdd7b3))
*   Improve printing of details ([cf6a4086](cf6a4086))

#### Bug Fixes

*   Don't abort with UNIQUE indexes, skip instead ([1b65f211](1b65f211))
*   Skip indexes with no bloat ([29383e8d](29383e8d))
*   Make Database required ([23bc632e](23bc632e))
*   Exclude tables, only use indexes ([1127b782](1127b782))



