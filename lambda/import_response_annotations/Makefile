TOOL_NAME=import_response_annotations
BUILD_DIR=../../build/${TOOL_NAME}
PACKAGES_DIR=../../build/packages/${TOOL_NAME}

.PHONY: build
build:
	rm -rf ${BUILD_DIR}
	rm -rf ${PACKAGES_DIR}
	rm -rf code/package
	mkdir -p -- ${BUILD_DIR} ${PACKAGES_DIR}/python
	docker run --rm -v "${PWD}:/var/task" -w /var/task --platform linux/amd64 python:3.12 \
		sh -c "pip install uv && uv pip install -r code/requirements.txt --target code/package"
	cp code/main.py ${BUILD_DIR}/
	cp -r code/package/* ${PACKAGES_DIR}/python/
