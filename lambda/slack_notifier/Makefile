TOOL_NAME=slack_notifier
BUILD_DIR=../build/${TOOL_NAME}

.PHONY: build
build:
	rm -rf ${BUILD_DIR}
	rm -rf code/package
	mkdir -p -- ${BUILD_DIR}
	uv pip install -r code/requirements.txt --target code/package
	cp code/main.py ${BUILD_DIR}/
	cp -r code/package/* ${BUILD_DIR}/
