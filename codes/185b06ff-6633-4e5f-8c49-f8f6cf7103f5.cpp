#include <bits/stdc++.h>
using namespace std;

int main() {
    string s;
    // Read the whole line as input
    getline(cin, s);

    // Reverse the string
    reverse(s.begin(), s.end());

    // Print the reversed string
    cout << s << endl;

    return 0;
}