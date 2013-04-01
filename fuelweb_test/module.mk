
$(call assert-variable,iso.path)
# $(call assert-variable,centos.path)

LEVEL ?= INFO
BUILD_DIR)/test/

$/%: /:=$/

test: test-integration

.PHONY: test-integration
test-integration: $(BUILD_DIR)/iso/iso.done
	ENV_NAME=$(ENV_NAME) ISO=$(abspath $(iso.path)) LOGS_DIR=$(LOGS_DIR)\
	nosetests -l $(LEVEL) $(NOSEARGS)


.PHONY: clean-integration-test
clean-integration-test: /:=$/
clean-integration-test:
	dos.py erase $(ENV_NAME) || true