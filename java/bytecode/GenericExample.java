package java.bytecode;

/**
 * 泛型示例 - 演示泛型类、泛型方法
 */
public class GenericExample<T extends Number> {
    
    private T genericField;
    
    public GenericExample(T value) {
        this.genericField = value;
    }
    
    // 泛型方法
    public <E> E genericMethod(E param) {
        return param;
    }
    
    // 泛型方法 - 多个类型参数
    public <K, V> void genericMethod2(K key, V value) {
        System.out.println("Key: " + key + ", Value: " + value);
    }
    
    public T getGenericField() {
        return genericField;
    }
    
    public void setGenericField(T genericField) {
        this.genericField = genericField;
    }
}

