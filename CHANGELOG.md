## Unreleased

<a name="v0.16.0"></a>
## v0.16.0 (2018-01-10)


#### Bug Fixes

*   Support lack of --exclude-index on some platforms ([4c16e976](4c16e976))

#### Features

*   Allow creation on separate tabelspaces ([41b8ba17](41b8ba17))



<a name="0.15.0"></a>
## 0.15.0 (2017-04-07)


#### Features

*   Add --exclude-index option to skip some indexes ([0c54f6b4](0c54f6b4))



<a name="0.14.0"></a>
## 0.14.0 (2017-03-30)


#### Bug Fixes

*   Always clean up and remove old broken indexes in error ([910b2913](910b2913))
*   When rebuilding an invalid, there'll be no 'primary' key ([50318b3b](50318b3b))
*   Don't wait more than 10 min to rename the old index ([16295c0d](16295c0d))
*   Try up to 10 times when making an invalid index ([b3b7c14b](b3b7c14b))
* **logging:**  Log when there is an exception ([4325c778](4325c778))
* **logs:**  Log that a thing is done, *after* you've done the thing ([1b776ce8](1b776ce8))
* **reindex:**  Don't leave INVALID indexes around ([68a36161](68a36161))

#### Features

*   Repair invalid indexes ([47ef09fa](47ef09fa))
*   Set application name, it appears in pg_stat_activity ([83d6de27](83d6de27))
*   add -v/--version argument to print version ([b1ca933b](b1ca933b))
* **logging:**
  *  Log more for index validity ([37a4dff7](37a4dff7))
  *  Log when index creation is successful ([9106badf](9106badf))



<a name="v0.13.0"></a>
## v0.13.0 (2016-09-05)


#### Features

*   Hostname support ([f5a111ce](f5a111ce))
* **output:**  Log duration of some (possibly long running) steps ([75230393](75230393))



<a name="v0.12.0"></a>
## v0.12.0 (2016-08-18)


#### Features

* **locking:**  Add a locking feature to prevent overlapping runs ([569b0315](569b0315))



<a name="v0.11.0"></a>
## v0.11.0 (2016-08-15)


#### Features

* **output:**  Print the currently installed version on startup ([98b1d339](98b1d339))



<a name="v0.10.0"></a>
## v0.10.0 (2016-08-11)


#### Bug Fixes

*   Better error handleing if cannot connect ([0b093063](0b093063))
* **output:**
  *  Typo fix ([21ce9300](21ce9300))
  *  Better error message when there's no waste ([9a9b409e](9a9b409e))
  *  Fix typo ([00b4448d](00b4448d))

#### Features

*   Close database connections when we're done with it ([41dd207a](41dd207a))
*   Add a --all-database option to run on all DBs ([f8d326ef](f8d326ef))
* **output:**  Log who we're connecting as ([7f51e2fd](7f51e2fd))



<a name="v0.9.0"></a>
## v0.9.0 (2016-08-04)


#### Features

* **output:**
  *  Allow logging to syslog and turn off logging to stdout ([19c55faf](19c55faf))
  *  Some slightly logging wording improvements ([205a4b18](205a4b18))



<a name="v0.8.0"></a>
## v0.8.0 (2016-07-27)


#### Bug Fixes

*   Attempt to work better if the disk fills up ([78ed8877](78ed8877))
*   Better formatting/printing when zero bytes ([7aec6855](7aec6855))
*   Don't index if <= min bloat ([54176ebd](54176ebd))

#### Features

*   Add --min-bloat option to skip tables with small bloat ([f3182715](f3182715))
*   Display running total of saved space ([4145d7b2](4145d7b2))
* **output:**  Minor improvements to logging output, esp w/ --dry-run ([e0992237](e0992237))



<a name="v0.7.0"></a>
## v0.7.0 (2016-04-29)


#### Features

*   Add --super-slim-mode which will drop the index ([ffc8e273](ffc8e273))



<a name="v0.6.0"></a>
## v0.6.0 (2016-04-15)


#### Bug Fixes

*   Show bytes as whole numbers not floats ([4dfae2f6](4dfae2f6))
*   Properly count the amount saved. ([6feafb4a](6feafb4a))
*   Continue to work with zero wastage and usage ([18aa6931](18aa6931))



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



