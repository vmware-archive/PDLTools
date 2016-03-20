Contributing to PDLTools
=========================
If you're a Pivotal employee and would like to contribute to PDLTools, this guide is for you. Following these step-by-step instructions you should be able to easily add your module to PDLTools.

1. Since you may not have push access to the master repo, fork the base repo [pivotalsoftware/PDLTools](https://github.com/pivotalsoftware/PDLTools), into your own account on GitHub.
2. Clone your forked repo into a VM. You can download the GPDB sandbox VM here: [GPDB Sandbox](https://network.pivotal.io/products/pivotal-gpdb#/releases/567/file_groups/337). Make sure you create an account on [PivNet](http://network.pivotal.io). You can get the latest GPDB sandbox VMs by going directly to [greenplum.org](http://greenplum.org)
3. Create a branch to keep track of your contribution: `git checkout -b my_contribution`
4. Look at the sample contribution in the branch named [sample_contribution](https://github.com/pivotalsoftware/PDLTools/tree/sample_contribution) on PDLTools. The changelist associated with the commit [sample_contribution_kl_divergence](https://github.com/pivotalsoftware/PDLTools/commit/9a0980a1b2b64a1a04c7ecfa76b233273779d191) should give you an idea of the list of files that you'll have to modify when you contribute a new module. Your contribution should include unit tests to validate the functionalities in your module. Also ensure your contribution is well documented. You can navigate to the `$BUILD/doc/user/html/index.html` or `$BUILD/doc/user/latex/refman.pdf` files in your local repo to check if the documentation for your contribution is appearing as expected on Doxygen docs.
5. Commit your changes to your branch (ex: `my_contribution`) on your GitHub account.
6. Submit a pull-request from the branch you created on your head fork (ex: vatsan/PDLTools) to the same branch on the basefork (pivotalsoftware/PDLTools).
![pdltools_sample_pull_request_1](https://github.com/pivotalsoftware/PDLTools/blob/master/doc/imgs/pdltools_sample_pull_request_1.png)
![pdltools_sample_pull_request_2](https://github.com/pivotalsoftware/PDLTools/blob/master/doc/imgs/pdltools_sample_pull_request_2.png)
7. This will automatically trigger a Travis CI build. If your contribution had no errors, you should see something like the following on CI.
![Travis-CI success](https://github.com/pivotalsoftware/PDLTools/blob/master/doc/imgs/pdltools_sample_travis.png)
The committers to PDLTools will see the following:
![Travis-CI success committer view](https://github.com/pivotalsoftware/PDLTools/blob/master/doc/imgs/pdltools_pull_request_travis_success.png)
8. The committers to pivotalsoftware/PDLTools will then merge your contribution to the base fork and voila, you should be able to see your contribution on [PDLTools User Docs](http://pivotalsoftware.github.io/PDLTools/). When a release is eventually created off the main branch, the installers for that release will contain your module.
 
