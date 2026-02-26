#pragma once

#include <cmath>

namespace math3d {

struct vec3d {
    float x, y, z;

    vec3d operator+(const vec3d& r) const { return {x+r.x, y+r.y, z+r.z}; }
    vec3d operator-(const vec3d& r) const { return {x-r.x, y-r.y, z-r.z}; }
    vec3d operator*(float s)        const { return {x*s, y*s, z*s}; }
    vec3d operator/(float s)        const { return {x/s, y/s, z/s}; }

    float length()        const { return sqrtf(x*x + y*y + z*z); }
    vec3d normalized()    const { return *this / length(); }

    static float dot(const vec3d& a, const vec3d& b) {
        return a.x*b.x + a.y*b.y + a.z*b.z;
    }
    static vec3d cross(const vec3d& a, const vec3d& b) {
        return {
            a.y*b.z - a.z*b.y,
            a.z*b.x - a.x*b.z,
            a.x*b.y - a.y*b.x
        };
    }
};

struct mat4 {
    float m[4][4];  // column-major: m[col][row]

    static mat4 identity() {
        mat4 r{};
        for (int i = 0; i < 4; i++) r.m[i][i] = 1.0f;
        return r;
    }

    mat4 operator*(const mat4& b) const {
        mat4 r{};
        for (int col = 0; col < 4; col++)
            for (int row = 0; row < 4; row++)
                for (int k = 0; k < 4; k++)
                    r.m[col][row] += m[k][row] * b.m[col][k];
        return r;
    }

    // Transforms a point (w=1); perspective divide applied.
    vec3d operator*(const vec3d& v) const {
        float x = v.x*m[0][0] + v.y*m[1][0] + v.z*m[2][0] + m[3][0];
        float y = v.x*m[0][1] + v.y*m[1][1] + v.z*m[2][1] + m[3][1];
        float z = v.x*m[0][2] + v.y*m[1][2] + v.z*m[2][2] + m[3][2];
        float w = v.x*m[0][3] + v.y*m[1][3] + v.z*m[2][3] + m[3][3];
        return {x/w, y/w, z/w};
    }

    // Transforms a direction (w=0); no translation, no perspective divide.
    vec3d transform_dir(const vec3d& v) const {
        return {
            v.x*m[0][0] + v.y*m[1][0] + v.z*m[2][0],
            v.x*m[0][1] + v.y*m[1][1] + v.z*m[2][1],
            v.x*m[0][2] + v.y*m[1][2] + v.z*m[2][2]
        };
    }
};

// Column-major convention throughout: T*R*S order composes left-to-right as expected.

static mat4 translate(const vec3d& t) {
    mat4 r = mat4::identity();
    r.m[3][0] = t.x;
    r.m[3][1] = t.y;
    r.m[3][2] = t.z;
    return r;
}

static mat4 rotateY(float angle) {
    mat4 r = mat4::identity();
    float c = cosf(angle);
    float s = sinf(angle);
    // Standard Y-rotation, column-major:
    //  col0       col2
    //  [ c, 0,-s] [s, 0, c]
    r.m[0][0] =  c;
    r.m[2][0] =  s;  // fixed: was -s
    r.m[0][2] = -s;  // fixed: was +s
    r.m[2][2] =  c;
    return r;
}

static mat4 rotateX(float angle) {
    mat4 r = mat4::identity();
    float c = cosf(angle);
    float s = sinf(angle);
    r.m[1][1] =  c;
    r.m[2][1] =  s;
    r.m[1][2] = -s;
    r.m[2][2] =  c;
    return r;
}

static mat4 rotateZ(float angle) {
    mat4 r = mat4::identity();
    float c = cosf(angle);
    float s = sinf(angle);
    r.m[0][0] =  c;
    r.m[1][0] =  s;
    r.m[0][1] = -s;
    r.m[1][1] =  c;
    return r;
}

static mat4 scale(const vec3d& s) {
    mat4 r = mat4::identity();
    r.m[0][0] = s.x;
    r.m[1][1] = s.y;
    r.m[2][2] = s.z;
    return r;
}

// Right-handed, camera looking down -Z, output NDC z in [-1, 1].
static mat4 perspective(float fov, float aspect, float near, float far) {
    mat4 r{};
    float f = 1.0f / tanf(fov * 0.5f);
    r.m[0][0] = f / aspect;
    r.m[1][1] = f;
    r.m[2][2] = (far + near) / (near - far);
    r.m[2][3] = -1.0f;
    r.m[3][2] = (2.0f * far * near) / (near - far);
    return r;
}

// Look-at view matrix. Produces world-to-camera transform.
static mat4 look_at(const vec3d& eye, const vec3d& target, const vec3d& up) {
    vec3d f = (target - eye).normalized();         // forward (-Z in view space)
    vec3d r = vec3d::cross(f, up).normalized();    // right
    vec3d u = vec3d::cross(r, f);                  // reorthogonalized up

    mat4 m{};
    m.m[0][0] =  r.x; m.m[1][0] =  r.y; m.m[2][0] =  r.z;
    m.m[0][1] =  u.x; m.m[1][1] =  u.y; m.m[2][1] =  u.z;
    m.m[0][2] = -f.x; m.m[1][2] = -f.y; m.m[2][2] = -f.z;
    m.m[3][0] = -vec3d::dot(r, eye);
    m.m[3][1] = -vec3d::dot(u, eye);
    m.m[3][2] =  vec3d::dot(f, eye);
    m.m[3][3] = 1.0f;
    return m;
}

} // namespace math3d