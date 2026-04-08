TOOL_NAME=import_candidate_themes
BUILD_DIR=../../build/${TOOL_NAME}
PACKAGES_DIR=../../build/packages/${TOOL_NAME}

.PHONY: build
build:
	rm -rf ${BUILD_DIR}
	rm -rf ${PACKAGES_DIR}
	rm -rf code/package
	mkdir -p -- ${BUILD_DIR} ${PACKAGES_DIR}/python
	pip install uv && uv pip install -r code/requirements.txt --target code/package
	cp code/main.py ${BUILD_DIR}/
	cp -r code/package/* ${PACKAGES_DIR}/python/
