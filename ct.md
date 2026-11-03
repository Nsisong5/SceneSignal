(myweasyprintenv) root@localhost:/sdcard/SceneSignal# python -m scene_signal inspect tests/fixtures/media/rotated_90_5s.mp4
Media file not found: tests/fixtures/media/rotated_90_5s.mp4
Traceback (most recent call last):
  File "/sdcard/SceneSignal/src/scene_signal/cli.py", line 141, in main
    inspection = adapter.inspect(args.file)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/sdcard/SceneSignal/src/scene_signal/adapters/media/ffprobe.py", line 32, in inspect
    raise ExtractionError(
scene_signal.domain.errors.ExtractionError: Media file not found: tests/fixtures/media/rotated_90_5s.mp4

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/sdcard/SceneSignal/src/scene_signal/__main__.py", line 6, in <module>
    main()
  File "/sdcard/SceneSignal/src/scene_signal/cli.py", line 272, in main
    sys.exit(2 if e.code in (ErrorCode.INVALID_JOB_CONTRACT, ErrorCode.UNSUPPORTED_CONTRACT_VERSION, ErrorCode.ASSET_NOT_FOUND) else 1)
                             ^^^^^^^^^
NameError: name 'ErrorCode' is not defined
(myweasyprintenv) root@localhost:/sdcard/SceneSignal#