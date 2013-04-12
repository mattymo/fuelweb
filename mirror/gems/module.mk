$(BUILD_DIR)/mirror/gems/gems-bundle/Gemfile: $(call depv,MIRROR_GEMS)
$(BUILD_DIR)/mirror/gems/gems-bundle/Gemfile:
	mkdir -p $(@D)
	echo -n > $@
	for i in $(MIRROR_GEMS); do \
		echo "source \"$$i\"" >> $@; \
	done

$(BUILD_DIR)/mirror/gems/gems-bundle/naily/Gemfile: $(call depv,MIRROR_GEMS)
$(BUILD_DIR)/mirror/gems/gems-bundle/naily/Gemfile: \
		$(BUILD_DIR)/packages/gems/build.done \
		$(BUILD_DIR)/packages/rpm/build.done
	mkdir -p $(@D)
	echo -n > $@
	for i in $(MIRROR_GEMS); do \
		echo "source \"file://$(SOURCE_DIR)/$(LOCAL_MIRROR_GEMS)\"" >> $@; \
		echo "source \"file://`readlink -f $(LOCAL_MIRROR_GEMS)`\"" >> $@; \
		echo "source \"$$i\"" >> $@; \
	done
	echo "gem 'naily', '$(NAILY_VERSION)'" >> $@
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/gems/gems-bundle-gemfile.done: \
		requirements-gems.txt \
		$(BUILD_DIR)/mirror/gems/gems-bundle/Gemfile \
		$(BUILD_DIR)/mirror/gems/gems-bundle/naily/Gemfile
	mkdir -p $(BUILD_DIR)/mirror/gems/gems-bundle
	cat requirements-gems.txt | while read gem ver; do \
		echo "gem \"$${gem}\", \"$${ver}\"" >> $(BUILD_DIR)/mirror/gems/gems-bundle/Gemfile; \
	done
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/gems/gems-bundle.done: $(BUILD_DIR)/mirror/gems/gems-bundle-gemfile.done
	( cd $(BUILD_DIR)/mirror/gems/gems-bundle && bundle install --path=. && bundle package )
	( cd $(BUILD_DIR)/mirror/gems/gems-bundle/naily && bundle install --path=. && bundle package )
	( cd $(BUILD_DIR)/mirror/gems/gems-bundle/vendor/cache/ && \
		gem fetch `for i in $(MIRROR_GEMS); do echo -n "--source $$i "; done` -v 1.3.4 bundler )
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/gems/build.done: $(call depv,LOCAL_MIRROR_GEMS)
$(BUILD_DIR)/mirror/gems/build.done: $(BUILD_DIR)/mirror/gems/gems-bundle.done
	@mkdir -p $(LOCAL_MIRROR_GEMS)/gems
	cp $(BUILD_DIR)/mirror/gems/gems-bundle/vendor/cache/*.gem $(LOCAL_MIRROR_GEMS)/gems
	cp $(BUILD_DIR)/mirror/gems/gems-bundle/naily/vendor/cache/*.gem $(LOCAL_MIRROR_GEMS)/gems
	(cd $(LOCAL_MIRROR_GEMS) && gem generate_index gems)
	$(ACTION.TOUCH)
