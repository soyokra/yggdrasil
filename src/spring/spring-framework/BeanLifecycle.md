# Bean的生命周期
Bean的生命周期包含三个部分：类文件和注册信息，BeanDefinition，Bean。两个步骤：注册BeanDefinition，注册Bean

![bean_lifecycle_001](bean_lifecycle_001.png)

## Bean注册方式

### xml方式

```xml
<bean id="myBean" 
      class="com.example.MyClass" 
      scope="singleton" 
      factory-method="createInstance" 
      factory-bean="myFactoryBean" 
      init-method="init" 
      destroy-method="cleanup" 
      autowire="byType" 
      dependency-check="all" 
      lazy-init="true" 
      primary="true" 
      abstract="false" 
      abstract="true">
    
    <property name="propertyName" value="propertyValue"/>
    <property name="anotherProperty" ref="anotherBean"/>
    
    <constructor-arg index="0" value="constructorValue"/>
    <constructor-arg index="1" ref="anotherBean"/>
    
    <qualifier value="specificBean"/>
    <lookup-method method="getBean" bean="myBean"/>
</bean>
```

### 注解方式
- @Bean注解
- @Component注解(@Repository, @Service, @Controller, @Configuration) + @ComponentScan
- @Import注解，@ImportSource注解，ImportSelect接口

## BeanDefinition
BeanDefinition是一个接口，实际上可能有多种BeanDefinition类：
```
- RootBeanDefinition
   - AbstractBeanDefinition
      - BeanMetadataAttributeAccessor
      - BeanDefinition
         - AttributeAccessor
         - BeanMetadataElement
- AnnotatedGenericBeanDefinition
   - GenericBeanDefinition
      - AbstractBeanDefinition
   - AnnotatedBeanDefinition
      - BeanDefinition
- ChildBeanDefinition
   - AbstractBeanDefinition
- ScannedGenericBeanDefinition
   - GenericBeanDefinition
   - AnnotatedBeanDefinition
```

注解类型的类和接口是通过执行BeanDefinitionRegistryPostProcessor接口的postProcessBeanDefinitionRegistry方法注册
的，核心实现类如下

- ConfigurationClassPostProcessor
- ConfigurationClass
- ConfigurationClassBeanDefinitionReader

执行顺序上，
1. 扫描启动对象sprivalApplication的基础目录下所有@Component注解的类，转化为ConfigurationClass对象
2. 处理@Import和ImportSelector接口的类，转化为ConfigurationClass对象
3. 处理ConfigurationClass注册BeanDefinition

执行过程中有递归法，会扫描出100多个ConfigurationClass对象

## Bean
![bean_lifecycle_002](bean_lifecycle_002.png)