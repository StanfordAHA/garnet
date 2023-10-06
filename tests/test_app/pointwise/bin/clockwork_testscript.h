#ifndef RDAI_CLOCKWORK_WRAPPER
#define RDAI_CLOCKWORK_WRAPPER

#include "rdai_api.h"


#include <string.h>

namespace {
template<typename A, typename B>
inline A reinterpret(const B &b) {
    #if __cplusplus >= 201103L
    static_assert(sizeof(A) == sizeof(B), "type size mismatch");
    #endif
    A a;
    memcpy(&a, &b, sizeof(a));
    return a;
}
inline float float_from_bits(uint32_t bits) {
    return reinterpret<float, uint32_t>(bits);
}

  
struct bfloat16_t {

    static const int mantissa_bits = 7;
    static const uint16_t sign_mask = 0x8000;
    static const uint16_t exponent_mask = 0x7f80;
    static const uint16_t mantissa_mask = 0x007f;

    /// \name Constructors
    /// @{

    /** Construct from a float, double, or int using
     * round-to-nearest-ties-to-even. Out-of-range values become +/-
     * infinity.
     */
    // @{
    explicit bfloat16_t(float value);
    explicit bfloat16_t(double value);
    explicit bfloat16_t(int value);
    bfloat16_t(uint16_t value);
    // @}

    /** Construct a bfloat16_t with the bits initialised to 0. This represents
     * positive zero.*/
    bfloat16_t() = default;

    /// @}

    // Use explicit to avoid accidently raising the precision
    /** Cast to float */
    explicit operator float() const;
    /** Cast to double */
    explicit operator double() const;
    /** Cast to int */
    explicit operator int() const;
    operator uint16_t() const;

    /** \name Convenience "constructors"
     */
    /**@{*/

    /** Get a new bfloat16_t that represents zero
     * \param positive if true then returns positive zero otherwise returns
     *        negative zero.
     */
    static bfloat16_t make_zero(bool positive);

    /** Get a new float16_t that represents infinity
     * \param positive if true then returns positive infinity otherwise returns
     *        negative infinity.
     */
    static bfloat16_t make_infinity(bool positive);

    /** Get a new bfloat16_t that represents NaN (not a number) */
    static bfloat16_t make_nan();

    /** Get a new bfloat16_t with the given raw bits
     *
     * \param bits The bits conformant to IEEE754 binary16
     */
    static bfloat16_t make_from_bits(uint16_t bits);

    /**@}*/

    /** Return a new bfloat16_t with a negated sign bit*/
    bfloat16_t operator-() const;

    /** Arithmetic operators. */
    // @{
    bfloat16_t operator+(bfloat16_t rhs) const;
    bfloat16_t operator-(bfloat16_t rhs) const;
    bfloat16_t operator*(bfloat16_t rhs) const;
    bfloat16_t operator/(bfloat16_t rhs) const;
    bfloat16_t operator+=(bfloat16_t rhs) { return (*this = *this + rhs); }
    bfloat16_t operator-=(bfloat16_t rhs) { return (*this = *this - rhs); }
    bfloat16_t operator*=(bfloat16_t rhs) { return (*this = *this * rhs); }
    bfloat16_t operator/=(bfloat16_t rhs) { return (*this = *this / rhs); }
    // @}

    /** Comparison operators */
    // @{
    bool operator==(bfloat16_t rhs) const;
    bool operator!=(bfloat16_t rhs) const { return !(*this == rhs); }
    bool operator>(bfloat16_t rhs) const;
    bool operator<(bfloat16_t rhs) const;
    bool operator>=(bfloat16_t rhs) const { return (*this > rhs) || (*this == rhs); }
    bool operator<=(bfloat16_t rhs) const { return (*this < rhs) || (*this == rhs); }
    // @}

    /** Properties */
    // @{
    bool is_nan() const;
    bool is_infinity() const;
    bool is_negative() const;
    bool is_zero() const;
    // @}

    /** Returns the bits that represent this bfloat16_t.
     *
     *  An alternative method to access the bits is to cast a pointer
     *  to this instance as a pointer to a uint16_t.
     **/
    uint16_t to_bits() const;

private:
    // The raw bits.
    uint16_t data = 0;
};

//static inline
//bfloat16_t int_to_float(const hw_uint<16>& in) {
//  return (bfloat16_t) in.to_int();
//}
//
//static inline
//bfloat16_t to_float(const hw_uint<16>& in) {
//  int i = in.to_int();
//  void* ip = (void*)(&i);
//  float* f = (float*) ip;
//  return (*f);
//}

union {
  uint32_t val;
  float f;
} union_var;

uint16_t round_to_even(float a) {
  //uint32_t e = reinterpret_cast<uint32_t&>(a);
  union_var.f = a;
  uint32_t e = union_var.val;
  
  // round float to even, comment out this codeblock for truncation
  uint32_t half = 0x00008000;
  uint32_t sum = e + half;
  
  // check if bottom bits are all zero
  uint32_t mantissa_mask = 0x0000ffff;
  bool is_zeroed = (sum & mantissa_mask) == 0;
  
  // clear last bit (round even) on tie
  uint32_t clear_mask = ~( ((uint32_t)is_zeroed) << 16);
  e = sum & clear_mask;

  // clear bottom bits
  e = e >> 16;

  //return bfloat16_t::make_from_bits(float_to_bfloat16( expf(bfloat16_to_float(a.to_bits())) ));
  //return bfloat16_t::make_from_bits( (uint16_t)e );
  return (uint16_t)e;
}

// Similar routines for bfloat. It's somewhat simpler.
uint16_t float_to_bfloat16(float f) {
    //uint16_t ret[2];
    //memcpy(ret, &f, sizeof(float));
    //// Assume little-endian floats
    //return ret[1];
    round_to_even(f);
}

float bfloat16_to_float(uint16_t b) {
    // Assume little-endian floats
    uint16_t bits[2] = {0, b};
    float ret;
    memcpy(&ret, bits, sizeof(float));
    return ret;
}

bfloat16_t::bfloat16_t(float value) : data(float_to_bfloat16(value)) {}

bfloat16_t::bfloat16_t(double value) : data(float_to_bfloat16(value)) {}

bfloat16_t::bfloat16_t(int value) : data(float_to_bfloat16(value)) {}

bfloat16_t::bfloat16_t(uint16_t value) : data(value) {}

bfloat16_t::operator float() const {
    return bfloat16_to_float(data);
}

bfloat16_t::operator double() const {
    return bfloat16_to_float(data);
}

bfloat16_t::operator int() const {
    return bfloat16_to_float(data);
}

bfloat16_t::operator uint16_t() const {
    return data;
}


bfloat16_t bfloat16_t::make_from_bits(uint16_t bits) {
    bfloat16_t f;
    f.data = bits;
    return f;
}

bfloat16_t bfloat16_t::make_zero(bool positive) {
    uint16_t bits = positive ? 0 : sign_mask;
    return bfloat16_t::make_from_bits(bits);
}

bfloat16_t bfloat16_t::make_infinity(bool positive) {
    uint16_t bits = exponent_mask | (positive ? 0 : sign_mask);
    return bfloat16_t::make_from_bits(bits);
}

bfloat16_t bfloat16_t::make_nan() {
    uint16_t bits = exponent_mask | mantissa_mask;
    return bfloat16_t::make_from_bits(bits);
}

bfloat16_t bfloat16_t::operator-() const {
    return bfloat16_t(-bfloat16_to_float(data));
}

bfloat16_t bfloat16_t::operator+(bfloat16_t rhs) const {
    return bfloat16_t(bfloat16_to_float(data) + bfloat16_to_float(rhs.data));
}

bfloat16_t bfloat16_t::operator-(bfloat16_t rhs) const {
    return bfloat16_t(bfloat16_to_float(data) - bfloat16_to_float(rhs.data));
}

bfloat16_t bfloat16_t::operator*(bfloat16_t rhs) const {
    return bfloat16_t(bfloat16_to_float(data) * bfloat16_to_float(rhs.data));
}

bfloat16_t bfloat16_t::operator/(bfloat16_t rhs) const {
    return bfloat16_t(bfloat16_to_float(data) / bfloat16_to_float(rhs.data));
}

bool bfloat16_t::operator==(bfloat16_t rhs) const {
    return bfloat16_to_float(data) == bfloat16_to_float(rhs.data);
}

bool bfloat16_t::operator>(bfloat16_t rhs) const {
    return bfloat16_to_float(data) > bfloat16_to_float(rhs.data);
}

bool bfloat16_t::operator<(bfloat16_t rhs) const {
    return bfloat16_to_float(data) < bfloat16_to_float(rhs.data);
}

bool bfloat16_t::is_nan() const {
    return ((data & exponent_mask) == exponent_mask) && (data & mantissa_mask);
}

bool bfloat16_t::is_infinity() const {
    return ((data & exponent_mask) == exponent_mask) && !(data & mantissa_mask);
}

bool bfloat16_t::is_negative() const {
    return data & sign_mask;
}

bool bfloat16_t::is_zero() const {
    return !(data & ~sign_mask);
}

uint16_t bfloat16_t::to_bits() const {
    return data;
}

static
inline bfloat16_t bfloat_from_bits(uint32_t bits) {
    return bfloat16_t(float_from_bits(bits));
}
}

/**
 * Run clockwork kernel pointwise

 * @param mem_obj_list List of input and output buffers
 * NOTE: last element in mem_obj_list points to output buffer
 *       whereas the remaining elements point to input buffers.
 */
void run_clockwork_program(RDAI_MemObject **mem_object_list);

#endif // RDAI_CLOCKWORK_WRAPPER