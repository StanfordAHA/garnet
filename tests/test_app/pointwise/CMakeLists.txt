add_executable(pointwise_process process.cpp)
halide_use_image_io(pointwise_process)

halide_generator(pointwise.generator SRCS pointwise_generator.cpp)

set(LIB pointwise)
halide_library_from_generator(${LIB}
  GENERATOR pointwise.generator)

target_link_libraries(pointwise_process PRIVATE ${LIB})
